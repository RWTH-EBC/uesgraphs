"""
This module includes the uesgraph to write a pandapipes model and simulation
"""

from datetime import datetime
from pathlib import Path
import os
import pandapipes as pp
import pandas as pd
import pandapower.control as control
from pandapipes.timeseries import run_timeseries
from pandapower.timeseries import DFData, OutputWriter
from datetime import datetime
from collections import defaultdict, deque
from tqdm import tqdm
import numpy as np

from uesgraphs.uesgraph import UESGraph
from uesgraphs import get_versioning_info

#For logging
import logging
import tempfile

def set_up_logger(name,log_dir = None,level=int(logging.ERROR)):
    """Sets up a configured logger with file handler.
    
    Creates a logger with specified name and logging level.
    Log files are stored in a directory with timestamp in filename.
    If no directory is specified, the system's temporary directory is used.
    
    Args:
        name (str): Name of the logger, also used for filename
        log_dir (str, optional): Directory for log files.
            Defaults to None (uses temp directory)
        level (int, optional): Logging level (e.g. logging.ERROR, logging.INFO).
            Defaults to logging.ERROR
    
    Returns:
        logging.Logger: Configured logger object
        
    Example:
        >>> logger = set_up_logger("my_app", "/var/log", logging.INFO)
        >>> logger.info("Application started")
        
    Notes:
        - Log filename format: {name}_{YYYYMMDD_HHMMSS}.log
        - Log entry format: time - logger_name - [file:line] - level - message
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if log_dir == None:
        log_dir = tempfile.gettempdir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    print(f"Logfile findable here: {log_file}")
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger   

def set_up_terminal_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a simple console-only logger for small functions.

    Args:
        name: Logger name
        level: Logging level (default: INFO)

    Returns:
        Configured console logger
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Console handler only
    console_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Prevent propagation to root logger to avoid double messages
    logger.propagate = False

    return logger

class SystemModelHeating(UESGraph):
    """Writes pandapipes model for system models from uesgraphs information

    While a uesgraph object uses edges and nodes to describe the network topology,
    the pandapipes model uses junctions and pipes. Therefore, each node in the uesgraph
    is represented by two junctions in the pandapipes model (supply and return). 
    At the current stage, only heating networks are supported.

    Attributes
    ----------
    stop_time : float
        Stop time for simulation in seconds
    timestep : float
        Timestep for simulation in seconds
    timesteps : int
        Number of timesteps for simulation calculated from 'timestep' and 'stop_time'
    graph["T_ground"] : list
        Ground temperature in Kelvin
    pp_network : pp.net
        Pandapipes network object
    """
    def __init__(
        self,
        stop_time,
        timestep,
        network_type="heating",
        logger=None
    ):
        
        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.__init__")
        logger.info(f"=== Initializing SystemModelHeating ===")

        super(SystemModelHeating, self).__init__()

        self.time_step = timestep
        self.stop_time = stop_time
        self.timesteps = int(self.stop_time / self.time_step)
        logger.debug(f"Timesteps number: '{self.timesteps}'")

        self.version_info = get_versioning_info()
        logger.debug(f"Version info: {self.version_info}")
        
        self.network_type = network_type
        logger.debug(f"Network type set to: '{self.network_type}'")
        
        self.demand_data = pd.DataFrame()

        self.graph["T_ground"] = [273.15 + 10]
        self.ground_temp_data = pd.DataFrame({"1.0 m": self.graph["T_ground"]}) 
        logger.debug(f"Default ground temperature: {self.graph['T_ground'][0] - 273.15:.2f} deg C")

        # Mapping for Supply and Return
        self.junction_map_supply = {}
        self.junction_map_return = {}

        self.pipe_map_supply = {}
        self.pipe_map_return = {}
    
        self.pp_network = pp.create_empty_network(fluid="water")

        self.heat_to_mass_factor = 0
        self.number_of_supplies = 1

        self.T_in = 0
        self.T_return = 0

        logger.info(f"SystemModelHeating initialization completed")

    def import_nodes_from_uesgraph(self, uesgraph_input, logger=None):
        """Imports nodes from UESGraph into pandapipes junctions.

        Parameters
        ----------
        uesgraph_input : uesgraphs.uesgraph.UESGraph object
            At current stage, this uesgraph should contain only 1 network of 1
            type that is indexed in the corrsponding nodelist as `'default'`
        logger : logging.Logger, optional
            Logger instance for debugging
        
        Returns
        -------
        Tuple[dict, int, int]
            Tuple containing:
            - junction_ids: Mapping of uesgraph node IDs to pandapipes junction IDs
            - heat_source_id: ID of the heat source junction
            - heat_source_r_id: ID of the heat source return junction
        """

        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.import_nodes_from_uesgraph")

        logger.info("=== Starting node import from UESGraph ===")
        logger.info("=== Starting node import from UESGraph (pandapipes) ===")
        junction_ids = {}
        heat_source_id = None
        heat_source_r_id = None

        p_in = 0
        p_return = 0
        T_in = 0
        T_return = 0
        dT_design = 0
        supplies = 0
        for node in uesgraph_input.nodes:
            try:
                node_data = uesgraph_input.nodes[node]
                pos = node_data["position"]

                # Supply-node (heating)
                if node_data["node_type"] == "building" and node_data.get("is_supply_heating", False):
                    if supplies == 0:
                        logger.debug(f"Creating supply node: {node}")
                        p_in = node_data["dpIn"]
                        p_return = node_data["pReturn"]
                        T_in = node_data["TIn"]
                        T_return = node_data["TReturn"]
                        self.T_in = T_in
                        self.T_return = T_return
                        supply_junction = pp.create_junction(
                            net=self.pp_network,
                            pn_bar=p_in,
                            tfluid_k=T_in,
                            name=f"{node}0",
                            geodata=(pos.x, pos.y),
                            position_x=pos.x,
                            position_y=pos.y
                        )
                        return_junction = pp.create_junction(
                            net=self.pp_network,
                            pn_bar=p_return,
                            tfluid_k=T_return,
                            name=f"{node}1",
                            geodata=(pos.x, pos.y),
                            position_x=pos.x,
                            position_y=pos.y
                        )
                        junction_ids[int(f"{node}0")] = supply_junction
                        junction_ids[int(f"{node}1")] = return_junction

                        self.junction_map_supply[supply_junction] = node
                        self.junction_map_return[return_junction] = node

                        heat_source_id = supply_junction
                        heat_source_r_id = return_junction

                        pp.create_circ_pump_const_pressure(
                            net=self.pp_network,
                            return_junction=return_junction,
                            flow_junction=supply_junction,
                            p_flow_bar=p_in,
                            plift_bar=p_in - p_return,
                            t_flow_k=T_in,
                            type="auto",
                            name="energy_hub"
                        )
                        supplies += 1
                    else:
                        logger.debug(f"Creating supply node: {node}")
                        p_in = node_data["dpIn"]
                        p_return = node_data["pReturn"]
                        T_in = node_data["TIn"]
                        T_return = node_data["TReturn"]
                        supply_junction = pp.create_junction(
                            net=self.pp_network,
                            pn_bar=p_in,
                            tfluid_k=T_in,
                            name=f"{node}0",
                            geodata=(pos.x, pos.y),
                            position_x=pos.x,
                            position_y=pos.y
                        )
                        between_junction = pp.create_junction(
                            net=self.pp_network,
                            pn_bar=p_in,
                            tfluid_k=T_in,
                            name=f"{node}01",
                            geodata=(pos.x, pos.y),
                            position_x=pos.x,
                            position_y=pos.y
                        )
                        return_junction = pp.create_junction(
                            net=self.pp_network,
                            pn_bar=p_return,
                            tfluid_k=T_return,
                            name=f"{node}1",
                            geodata=(pos.x, pos.y),
                            position_x=pos.x,
                            position_y=pos.y
                        )
                        junction_ids[int(f"{node}0")] = supply_junction
                        junction_ids[int(f"{node}01")] = between_junction
                        junction_ids[int(f"{node}1")] = return_junction

                        self.junction_map_supply[supply_junction] = node
                        self.junction_map_return[return_junction] = node

                        heat_source_id = supply_junction
                        heat_source_r_id = return_junction

                        #m_flow = /uesgraph_input.graph["number_of_supplies"]/(uesgraph_input.graph["dT_Net"]*uesgraph_input.graph["cp_default"])
                        m_flow = 0
                        logger.info(f"Mass flow for supply node '{node}': {m_flow:.4f} kg/s")

                        pp.create_circ_pump_const_mass_flow(
                            net=self.pp_network,
                            return_junction=return_junction,
                            flow_junction=between_junction,
                            p_flow_bar=p_in,
                            mdot_flow_kg_per_s = m_flow,
                            t_flow_k=T_in,
                            type="auto",
                            name="energy_hub"
                        )

                        pp.create_flow_control(
                            net=self.pp_network,
                            from_junction=between_junction,
                            to_junction=supply_junction,
                            controlled_mdot_kg_per_s=m_flow,
                            name="supply",
                        )

                # Building nodes (heating)
                elif node_data["node_type"] == "building":
                    logger.debug(f"Creating building node: {node}")
                    dT_design = node_data["dTDesign"]
                    supply_junction = pp.create_junction(
                        net=self.pp_network,
                        pn_bar=p_in,
                        tfluid_k=T_in,
                        name=f"{node}0",
                        geodata=(pos.x, pos.y),
                        position_x=pos.x,
                        position_y=pos.y
                    )
                    return_junction = pp.create_junction(
                        net=self.pp_network,
                        pn_bar=p_in,
                        tfluid_k=T_return,
                        name=f"{node}1",
                        geodata=(pos.x, pos.y),
                        position_x=pos.x,
                        position_y=pos.y
                    )
                    junction_ids[int(f"{node}0")] = supply_junction
                    junction_ids[int(f"{node}1")] = return_junction

                    self.junction_map_supply[supply_junction] = node
                    self.junction_map_return[return_junction] = node

                    heat_demand_w = node_data["input_heat"][0]

                    pp.create_heat_consumer(
                        net=self.pp_network,
                        from_junction=supply_junction,
                        to_junction=return_junction,
                        deltat_k=dT_design,
                        qext_w=heat_demand_w,
                        name=node_data["name"]
                    )

                # network nodes
                elif node_data["node_type"].startswith("network"):
                    logger.debug(f"Creating network node: {node}")
                    supply_junction = pp.create_junction(
                        net=self.pp_network,
                        pn_bar=p_in,
                        tfluid_k=T_in,
                        name=f"{node}0",
                        geodata=(pos.x, pos.y),
                        position_x=pos.x,
                        position_y=pos.y
                    )
                    return_junction = pp.create_junction(
                        net=self.pp_network,
                        pn_bar=p_return,
                        tfluid_k=T_return,
                        name=f"{node}1",
                        geodata=(pos.x, pos.y),
                        position_x=pos.x,
                        position_y=pos.y
                    )
                    junction_ids[int(f"{node}0")] = supply_junction
                    junction_ids[int(f"{node}1")] = return_junction

                    self.junction_map_supply[supply_junction] = node
                    self.junction_map_return[return_junction] = node
                else:
                    logger.warning(f"Node type not supported: {node_data.get('node_type')}")

            except KeyError as e:
                logger.error(f"Key error for node {node}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for node {node}: {e}")

        return junction_ids, heat_source_id, heat_source_r_id

    def import_edges_from_uesgraph(self, uesgraph_input, junction_ids, logger=None):
        """Imports edges from UESGraph into pandapipes pipes.

        Parameters
        ----------
        uesgraph_input : uesgraphs.uesgraph.UESGraph object
            At current stage, this uesgraph should contain only 1 network of 1
            type that is indexed in the corrsponding nodelist as `'default'`
        junction_ids : dict
            Mapping of uesgraph node IDs to pandapipes junction IDs
        logger : logging.Logger, optional
            Logger instance for debugging

        Returns
        -------
        Tuple[list, dict]
            Tuple containing:
            - pipe_list: List of pipes with their details
        """

        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.import_pipes_from_uesgraph")
            
        logger.info("=== Starting pipe import from UESGraph ===")
        pipe_list = []
        pipe_index = 0
        for edge in uesgraph_input.edges():
            try:
                from_node, to_node = edge
                d_in, _ = self.find_pipe_parameter(uesgraph_input.edges[edge]["diameter"] * 1000)
                edge_data = uesgraph_input.edges[edge]
                heat_trans = 1 / (edge_data["dIns"]/ edge_data["kIns"])
                loss_coefficient = self.estimate_xi(uesgraph_input.edges[edge]["length"])
                T_ground = self.graph["T_ground"][0]

                for idx, pipe_type in enumerate(["supply", "return"]):
                    pipe = pp.create_pipe_from_parameters(
                        net=self.pp_network,
                        from_junction=junction_ids[int(f"{from_node}{idx}")],
                        to_junction=junction_ids[int(f"{to_node}{idx}")],
                        length_km=uesgraph_input.edges[edge]["length"]/1000,
                        diameter_m=d_in,
                        k_mm=edge_data["roughness"],
                        loss_coefficient=loss_coefficient,
                        u_w_per_m2k=heat_trans,
                        sections=edge_data["sections"],
                        text_k=T_ground,
                        name=f"{pipe_type}_{uesgraph_input.edges[edge]['diameter']}_{uesgraph_input.edges[edge]['pipeID']}"
                    )
                    pipe_list.append({
                        "index": pipe_index, 
                        "from": junction_ids[int(str(edge[0]) + f"{idx}")],
                        "to": junction_ids[int(str(edge[1]) + f"{idx}")],
                        "type": pipe_type,
                        "edge": edge,
                        "flow_change": False,
                    })
                    pipe_index += 1
                
                self.pipe_map_supply[pipe] = edge
                self.pipe_map_return[pipe] = edge

            except KeyError as e:
                logger.error(f"Key error for edge {edge}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for edge {edge}: {e}")

        return pipe_list

    def import_from_uesgraph(self, uesgraph_input, logger=None):
        """Imports full UESGraph into pandapipes model.

        Parameters
        ----------

        uesgraph_input : uesgraphs.uesgraph.UESGraph object
            At current stage, this uesgraph should contain only 1 network of 1
            type that is indexed in the corrsponding nodelist as `'default'`
        logger : logging.Logger, optional
            Logger instance for debugging
        
        Returns
        -------
        Tuple[dict, list, dict, int, int]
            Tuple containing:
            - junction_ids: Mapping of uesgraph node IDs to pandapipes junction IDs
            - pipe_list: List of pipes with their details
            - heat_source_id: ID of the heat source junction
            - heat_source_r_id: ID of the heat source return junction
        """

        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.import_from_uesgraph")
        
        logger.info("=== Starting full UESGraph import (pandapipes) ===")
        self.heat_to_mass_factor = 1/uesgraph_input.graph["number_of_supplies"]/(uesgraph_input.graph["dT_Net"]*uesgraph_input.graph["cp_default"])
        self.number_of_supplies = uesgraph_input.graph["number_of_supplies"]

        # Step 1: Junctions
        junction_ids, heat_source_id, heat_source_r_id = self.import_nodes_from_uesgraph(
            uesgraph_input, logger=logger
        )

        # Step 2: Pipes
        pipe_list = self.import_edges_from_uesgraph(
            uesgraph_input, junction_ids, logger=logger
        )

        data = {}
        max_len = 0

        for node in uesgraph_input.nodes:
            node_data = uesgraph_input.nodes[node]
            # only take buildings
            if node_data.get("node_type") != "building" or node_data.get("is_supply_heating", False):
                continue
            heat_list = node_data.get("input_heat", [])
            dhw_list = node_data.get("input_dhw", [0.0] * len(heat_list))
            heat = [h + d for h, d in zip(heat_list, dhw_list)]
            data[node] = heat
            max_len = max(max_len, len(heat))

        df = pd.DataFrame()

        # add each node’s column
        for node, vals in data.items():
            # pad shorter lists if needed
            node_name = uesgraph_input.nodes[node]["name"]
            padded = vals + [None] * (max_len - len(vals))
            df[node_name] = padded

        self.demand_data = df

        logger.info(f"Import completed: {len(junction_ids)} junctions, {len(pipe_list)} pipes")
        return junction_ids, pipe_list, heat_source_id, heat_source_r_id
    
    def find_pipe_parameter(self, pipe_dn: float):
        """Finds the inner diameter and insulation thickness for a given nominal pipe diameter.

        Uses a lookup table based on standard district heating pipe dimensions for
        insulation class 3 according to district heating planning handbook.

        Args:
            pipe_dn (float): Nominal pipe diameter in mm

        Returns:
            Tuple[float, float]: Inner diameter in meters, insulation thickness in meters

        Note:
            If the exact pipe diameter is not in the reference table, the closest
            standard size will be selected.
        """
        # Standard pipe parameters: {DN: [inner_diameter (mm), insulation_thickness (mm)]}
        pipe_parameters = {
            21.6: [21.6, (125 - 26.9) / 2],
            28.5: [28.5, (125 - 33.7) / 2],
            37.2: [37.2, (140 - 42.4) / 2],
            43.1: [43.1, (140 - 48.3) / 2],
            54.5: [54.5, (160 - 60.3) / 2],
            70.3: [70.3, (180 - 76.1) / 2],
            82.5: [82.5, (200 - 88.9) / 2],
            107.1: [107.1, (250 - 114.3) / 2],
            132.5: [132.5, (280 - 139.7) / 2],
            160.3: [160.3, (315 - 168.3) / 2],
            200: [210.1, (400 - 219.1) / 2],
            250: [263.0, (500 - 273.0) / 2],
            300: [312.7, (580 - 323.9) / 2],
            350: [344.4, (630 - 355.6) / 2],
            400: [393.8, (730 - 406.4) / 2],
            450: [444.6, (800 - 457.2) / 2],
            500: [495.4, (900 - 508.0) / 2],
            600: [595.8, (1000 - 610.0) / 2],
            700: [695.0, (1100 - 711.0) / 2],
            800: [795.4, (1200 - 813.0) / 2],
            900: [894.0, (1300 - 914.0) / 2],
            1000: [994.0, (1400 - 1016.0) / 2],
        }

        # If pipe diameter not in table, find closest standard size
        if pipe_dn not in pipe_parameters.keys():
            dn_list = list(pipe_parameters.keys())
            pipe_dn = dn_list[
                min(range(len(dn_list)), key=lambda i: abs(dn_list[i] - pipe_dn))
            ]

        # Convert from mm to m
        diameter_in = pipe_dn * 1e-3
        insulation_thickness = pipe_parameters[pipe_dn][1] * 1e-3

        return diameter_in, insulation_thickness
    
    def estimate_xi(self, l_pipe: float):
        """Estimates the total loss coefficient for a pipe based on its length.

        Calculates pressure losses from:
        - 90° elbows (approx. every 25m a U-form with 4x90° elbows)
        - Tee junctions (flow separation and association at ends)
        - Installed slide valves

        Args:
            l_pipe (float): Length of the pipe in meters

        Returns:
            float: Total loss coefficient (xi) for the pipe

        References:
            - Horlacher2016, Rohrleitungen 2 (S.519-521)
            - Boehmer Fernwärme documentation (S.46)
        """
        xi_90 = 0.08  # Loss coefficient for 90° elbow
        xi_tee = 0.25  # Loss coefficient for tee junction
        xi_valve = 0.05  # Loss coefficient for slide valve

        # Calculate total loss coefficient:
        # - 4 elbows every 25m
        # - 2 tee junctions with 2/3 factor to account for junction of 3 pipes
        # - 2 slide valves
        xi_tot = 4 * int(l_pipe / 25) * xi_90 + 2 / 3 * 2 * xi_tee + 2 * xi_valve
        return xi_tot
    
    def run_test_simulation(self, logger=None):
        """Does a test simulation of the pandapipes network to check if it runs without errors.

        Parameters
        ----------
        logger : logging.Logger, optional
            Logger instance for debugging
        
        Raises
        ------
        Exception
            If the test simulation fails
        """

        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.run_test_simulation")

        logger.info("=== Starting pandapipes test simulation ===")

        logger.info(f"Circ_pump_pressure: {self.pp_network.circ_pump_pressure}")
        logger.info(f"Heat consumer: {self.pp_network.heat_consumer}")
        try:
            pp.pipeflow(
                net=self.pp_network,
                mode="sequential",
                stop_condition="tol",
                iter=100,
                tol_p=1e-7,
                tol_v=1e-7,
                tol_T=1e-3,
            )
            logger.info("✅ Test simulation finished successfully!")

        except Exception as e:
            logger.error(f"❌ Test simulation failed: {e}")
            raise
        
        logger.info(f"Circ_pump_pressure: {self.pp_network.res_circ_pump_pressure}")
        logger.info(f"Heat consumer: {self.pp_network.res_heat_consumer}")

    def pipe_order(self, pipe_list, heat_source_id, heat_source_r_id):
        pp.pipeflow(
            net=self.pp_network,
            mode="hydraulics",
            stop_condition="tol",
            iter=100,
            tol_p=1e-7,
            tol_v=1e-7,
            tol_T=1e-3,
        )
        """
            This part is responsible for the sorting of the pipes in the way that we get
            a list of the pipes names from the given heat source to the substations. After 
            that the way back from all substations to the heat source is found. This is 
            necessary later in the calculation of the temperature in the pipes, to prevent 
            calculating temperatures in pipes before all other temperatures before that were
            calculated. Layer-idea is based on Qin et al. (2019)
        """
        ###############################################################################
        for pipe in pipe_list:
            idx = pipe["index"]
            if self.pp_network.res_pipe["mdot_from_kg_per_s"][idx] < 0:
                pipe["from"], pipe["to"] = pipe["to"], pipe["from"]
                pipe["flow_change"] = True

        adjacency = defaultdict(list)         

        for pipe in pipe_list:
            idx = pipe["index"]
            f = pipe["from"]
            t = pipe["to"]
            adjacency[f].append(idx)

        layer_by_pipe = {}
        queue = deque()

        for pipe in pipe_list:
            if pipe["from"] == heat_source_id:
                layer_by_pipe[pipe["index"]] = 1
                queue.append(pipe["index"])

        # BFS-similar: Layer propagation
        while queue:
            current = queue.popleft()
            current_layer = layer_by_pipe[current]
            to_junc = pipe_list[current]["to"]

            for next_pipe_idx in adjacency.get(to_junc, []):
                prev_layer = layer_by_pipe.get(next_pipe_idx, 0)
                new_layer = current_layer + 1
                if new_layer > prev_layer:
                    layer_by_pipe[next_pipe_idx] = new_layer
                    queue.append(next_pipe_idx)

        supply_pipes = [p for p in pipe_list if p["type"] == "supply"]
        
        sorted_supply_pipes = sorted(
            supply_pipes, 
            key=lambda p: layer_by_pipe.get(p["index"], 9999)
        )

        return_pipes = [p for p in pipe_list if p["type"] == "return"]

        adj_return = defaultdict(list)

        for pipe in return_pipes:
            idx = pipe["index"]
            f = pipe["from"]
            t = pipe["to"]
            adj_return[t].append(idx)

        layer_by_pipe_return = {}
        queue = deque()

        for pipe in return_pipes:
            if pipe["to"] == heat_source_r_id:
                layer_by_pipe_return[pipe["index"]] = 1
                queue.append(pipe["index"])

        while queue:
            current = queue.popleft()
            current_layer = layer_by_pipe_return[current]
            end_junction = pipe_list[current]["from"]

            for next_pipe_idx in adj_return.get(end_junction, []):
                prev_layer = layer_by_pipe_return.get(next_pipe_idx, 0)
                new_layer = current_layer + 1
                if new_layer > prev_layer:
                    layer_by_pipe_return[next_pipe_idx] = new_layer
                    queue.append(next_pipe_idx)

        sorted_return_pipes = sorted(
            return_pipes,
            key=lambda p: layer_by_pipe_return.get(p["index"], 9999),
            reverse=True 
        )

        return sorted_supply_pipes, sorted_return_pipes, layer_by_pipe, layer_by_pipe_return


    def calculate_temperature_pipe_profile_implicit(self, T_in, T_prev, mdot, cp, alpha, d_in, T_ground, dx, dt, rho, sections):
        """
            This function calculates with an implicit euler scheme the temperature
            distribution within one pipe.

            Args:
                T_in (float): Inflow temperature of the pipe in K
                T_prev (list): Previous temperature distribution in the pipe, all values in K
                m_dot (float): Mass flow in the pipe in kg/s
                cp (float): Heat capacity in J/(kg K)
                alpha (float): Heat transfer coefficient in W/(m^2 K)
                d_in (float): Pipe diameter in m
                T_ground (float): Ground temperature in K
                dx (float): Step in the pipe length in m
                dt (float): Timestep in s
                rho (float): Density in kg/m^3
                sections (float): Number of sections

            Returns:
                list: Temperature distrubtion list in the pipe for the next time step

        """
        
        A = np.zeros((sections+1, sections+1))
        b = np.zeros(sections+1)
        
        F_conv = 4 * mdot / (rho * np.pi * d_in**2 * dx)
        F_loss = 4 * alpha / (rho * d_in * cp)
        
        A[0, 0] = 1
        b[0] = T_in

        for i in range(1, sections+1):
            A[i, i-1] = -dt * F_conv
            A[i, i] = 1 + dt * (F_conv + F_loss)
            b[i] = T_prev[i] + dt * F_loss * T_ground
        
        T_next = np.linalg.solve(A, b)
        return T_next.tolist()

    def mix_junction_temperatures(self, pp_network, pipe_temp_history, pipe_subset, logger=None):
        """
            This function calculates a mixing temperature if two pipes flow into one pipe.

            Args:
                pp_network (pandapipes-network): Pandapipes network
                pipe_temp_history (dict): Temperatures of pipes to different time steps
                pipe_subset (list): Pipes that are used to find the inflowing pipes

            Returns:
                ---

        """
        relevant_junctions = defaultdict(list)

        for pipe in pipe_subset:
            idx = pipe["index"]
            junc = pipe["to"]
            relevant_junctions[junc].append(pipe)
        

        for junc_id, pipes in relevant_junctions.items():
            numerator = 0
            denominator = 0
            i = 0
            for pipe in pipes:
                idx = pipe["index"]
                T_out = pipe_temp_history[idx][-1][-1]  # last timestep, last section
                if pipe["flow_change"]:
                    mdot = pp_network.res_pipe["mdot_to_kg_per_s"][idx]
                else:
                    mdot = pp_network.res_pipe["mdot_from_kg_per_s"][idx]
                if mdot > 0:
                    numerator += mdot * T_out
                    denominator += mdot
                else:
                    logger.info(f"mdot is negative for pipe {pipe['index']} with to_junction: {pipe['to']}")
                i+=1
            
            if denominator > 0:
                T_mixed = numerator / denominator
                pp_network.res_junction.loc[junc_id,"t_k"] = T_mixed

    """
        This part mimics the OutputWriter of pandapipes to have more control of logging
        current states, initializing the Writer and write the result in the same format.
    """
    ###############################################################################
    def init_output_writer(self, log_variables):
        output_data = {}
        for comp, var in log_variables:
            output_data[(comp, var)] = defaultdict(list)  
        output_data["time"] = []  
        return output_data

    def log_current_state(self, pp_network, output_data, log_variables, current_time):
        output_data["time"].append(current_time)

        for comp, var in log_variables:
            result_df = getattr(pp_network, comp)
            for idx in result_df.index:
                value = result_df.at[idx, var]
                output_data[(comp, var)][idx].append(value)

    def write_results_to_csv(self, output_data, log_variables, base_folder):
        os.makedirs(base_folder, exist_ok=True)
        
        times = output_data["time"]
        
        for comp, var in log_variables:
            comp_folder = os.path.join(base_folder, comp)
            os.makedirs(comp_folder, exist_ok=True)
            
            variable_data = output_data[(comp, var)]
            
            df = pd.DataFrame(variable_data, index=times)

            df.index.name = ""
            df.to_csv(os.path.join(comp_folder, f"{var}.csv"), sep=";")

    def run_timeseries_dpp_own(self, pipe_list, heat_source_id, heat_source_r_id, save_at, logger=None):
        # Create pipe order for temperature calculation
        sorted_supply_pipes, sorted_return_pipes, layer_by_pipe, layer_by_pipe_return = self.pipe_order(pipe_list, heat_source_id, heat_source_r_id)
        
        # Define output variables for the timeseries
        log_variables = [
            ("res_junction", "p_bar"),
            ("res_junction", "t_k"),
            ("res_heat_consumer", "t_from_k"),
            ("res_heat_consumer", "t_outlet_k"),
            ("res_heat_consumer", "mdot_from_kg_per_s"),
            ("res_heat_consumer", "p_from_bar"),
            ("res_heat_consumer", "p_to_bar"),
            ("res_circ_pump_pressure", "mdot_from_kg_per_s"),
            ("res_circ_pump_pressure", "t_from_k"),
            ("res_circ_pump_pressure", "deltat_k"),
            ("res_circ_pump_pressure", "qext_w"),
            ("res_circ_pump_pressure", "vdot_m3_per_s"),
            ("res_pipe", "v_mean_m_per_s"),
            ("res_pipe", "mdot_from_kg_per_s"),
            ("res_pipe", "p_from_bar"),
            ("res_pipe", "p_to_bar"),
        ]

        output_data = self.init_output_writer(log_variables)

        # Use the heat capacity values of the pandapipes simulation to calculate a mean
        # The value is slightly different from a constant value but is still valid
        cp_supply = pp.get_fluid(self.pp_network).get_property("heat_capacity", self.T_in + 273.15)
        rho_supply = pp.get_fluid(self.pp_network).get_property("density", self.T_in + 273.15)
        cp_return = pp.get_fluid(self.pp_network).get_property("heat_capacity", self.T_return + 273.15)

        # Setting time step
        self.time_step = 3600
        factor = int(3600/ self.time_step)
        self.timesteps *= factor
        self.demand_data = self.resample_profile_constant(self.demand_data, factor)
        self.ground_temp_data = self.resample_profile_constant(self.ground_temp_data, factor)

        dt = self.time_step
        n=0

        pipe_temperatures_history = {pipe["index"]: [[self.pp_network.res_pipe["t_from_k"][pipe["index"]]] * (self.pp_network.pipe["sections"][pipe["index"]] + 1)]
                                    for pipe in pipe_list}
        progress_bar = tqdm(total=self.timesteps, unit="it")

        # --- 5. Calculating temperatures ---
        logger.info("Starting pandapipes dynamic year-simulation ...")
        for t in range(0, (self.timesteps+1)*dt, dt):

            max_layer = max(layer_by_pipe.values())

            # Calculating temperatures from the heat source to the substations
            for layer in range(1, max_layer + 1):
                current_layer_pipes = [p for p in sorted_supply_pipes if layer_by_pipe.get(p["index"], 0) == layer]
                
                for pipe in current_layer_pipes:
                    idx = pipe["index"]
                    from_junc = pipe["from"]
                    to_junc = pipe["to"]
                    
                    T_in = self.pp_network.res_junction["t_k"][from_junc]
                    alpha = self.pp_network.pipe["u_w_per_m2k"][idx]
                    if pipe["flow_change"]:
                        mdot = self.pp_network.res_pipe["mdot_to_kg_per_s"][idx]
                    else:
                        mdot = self.pp_network.res_pipe["mdot_from_kg_per_s"][idx]
                    d_in = self.pp_network.pipe["diameter_m"][idx]
                    length = self.pp_network.pipe["length_km"][idx]*1000
                    sections = self.pp_network.pipe["sections"][idx]
                    T_ground = self.pp_network.pipe["text_k"][idx]
                    dx = length/sections
                    T_prev = pipe_temperatures_history[idx][-1]
                    T_next = self.calculate_temperature_pipe_profile_implicit(T_in, T_prev, mdot, cp_supply, alpha, d_in, T_ground, dx, dt, rho_supply, sections)
                    pipe_temperatures_history[idx].append(T_next)
                    if pipe["flow_change"]:
                        self.pp_network.res_pipe.loc[idx, "t_from_k"] = T_next[-1]
                    else:
                        self.pp_network.res_pipe.loc[idx, "t_to_k"] = T_next[-1]
                
                self.mix_junction_temperatures(self.pp_network, 
                    pipe_temperatures_history,
                    pipe_subset=current_layer_pipes)

            # Processing the heat consumer with constant dT to get the output for the return pipes 
            for consumer_id in range(len(self.pp_network.heat_consumer)):
                q_dot = self.pp_network.heat_consumer["qext_w"][consumer_id]  
                from_junc = self.pp_network.heat_consumer["from_junction"][consumer_id]
                to_junc = self.pp_network.heat_consumer["to_junction"][consumer_id]
                supply_pipe = self.pp_network.pipe[(self.pp_network.pipe["to_junction"] == from_junc)]
                return_pipe = self.pp_network.pipe[(self.pp_network.pipe["to_junction"] == to_junc)]

                pipe_idx = supply_pipe.index[0]
                
                m_dot = abs(self.pp_network.res_heat_consumer["mdot_from_kg_per_s"][consumer_id])
                T_vorlauf = self.pp_network.res_pipe["t_to_k"][pipe_idx]
                self.pp_network.res_heat_consumer.loc[consumer_id, "t_from_k"] = T_vorlauf

                cp_mean = (cp_supply + cp_return)/2

                T_rueck = T_vorlauf - q_dot/m_dot/cp_mean
                self.pp_network.res_heat_consumer.loc[consumer_id, "t_outlet_k"] = T_rueck
                self.pp_network.res_heat_consumer.loc[consumer_id, "t_to_k"] = T_rueck

                self.pp_network.res_heat_consumer.loc[consumer_id, "deltat_k"] = T_vorlauf - T_rueck

                pipe_idx = return_pipe.index[0]
                self.pp_network.res_junction.loc[to_junc, "t_k"]  = T_rueck

            max_layer_return = max(layer_by_pipe_return.values())

            # Calculating temperatures from the substations back to the heat source
            for layer in range(max_layer_return, 0, -1):  # Reverse order
                
                current_layer_return_pipes = [p for p in sorted_return_pipes if layer_by_pipe_return.get(p["index"], 0) == layer]

                for pipe in current_layer_return_pipes:
                    idx = pipe["index"]
                    from_junc = pipe["from"]
                    to_junc = pipe["to"]

                    T_in = self.pp_network.res_junction["t_k"][from_junc]
                    alpha = self.pp_network.pipe["u_w_per_m2k"][idx]
                    if pipe["flow_change"]:
                        mdot = self.pp_network.res_pipe["mdot_to_kg_per_s"][idx]
                    else:
                        mdot = self.pp_network.res_pipe["mdot_from_kg_per_s"][idx]
                    d_in = self.pp_network.pipe["diameter_m"][idx]
                    length = self.pp_network.pipe["length_km"][idx]*1000
                    sections = self.pp_network.pipe["sections"][idx]
                    T_ground = self.pp_network.pipe["text_k"][idx]
                    dx = length/sections
                    T_prev = pipe_temperatures_history[idx][-1]
                    T_next = self.calculate_temperature_pipe_profile_implicit(T_in, T_prev, mdot, cp_supply, alpha, d_in, T_ground, dx, dt, rho_supply, sections)
                    pipe_temperatures_history[idx].append(T_next)
                    if pipe["flow_change"]:
                        self.pp_network.res_pipe.loc[idx, "t_from_k"] = T_next[-1]
                    else:
                        self.pp_network.res_pipe.loc[idx, "t_to_k"] = T_next[-1]

                self.mix_junction_temperatures(self.pp_network, 
                    pipe_temperatures_history,
                    current_layer_return_pipes)
                
            return_junc = self.pp_network.circ_pump_pressure["return_junction"][0]
            self.pp_network.res_circ_pump_pressure.loc[0, "t_from_k"] = self.pp_network.res_junction["t_k"][return_junc]
            self.pp_network.res_circ_pump_pressure.loc[0, "deltat_k"] = self.pp_network.res_circ_pump_pressure["t_from_k"][0] - self.pp_network.res_circ_pump_pressure["t_to_k"][0]

            # Saving only for hours the temperatures and do new hydraulics simulation with new demand values
            if t == dt*(n+1):
                progress_bar.update(1)

                self.log_current_state(self.pp_network, output_data, log_variables, n)

                if n+1 == self.timesteps:
                    break

                for consumer_id in range(len(self.pp_network.heat_consumer)):
                    heat_demand_w = self.demand_data.iloc[n+1, consumer_id]
                    self.pp_network.heat_consumer.loc[consumer_id, "qext_w"] = heat_demand_w
                T_ground = self.ground_temp_data.loc[self.ground_temp_data.index[n+1], "1.0 m"]
                for pipe_id in range(len(self.pp_network.pipe)):
                    self.pp_network.pipe.loc[pipe_id, "text_k"] = T_ground
                pp.pipeflow(net=self.pp_network, mode="hydraulics",
                    stop_condition="tol",
                    iter=500,
                    tol_p=1e-7,
                    tol_v=1e-7,
                    tol_T=1e-3,
                )
                n+=1

        progress_bar.close()

        # Saving the results to the folder
        self.write_results_to_csv(output_data, log_variables, base_folder=save_at)

    def resample_profile_constant(self, df, factor):
        """
        Dupliziert jede Zeile `factor`-mal, damit ein Profil bei kleineren Zeitschritten
        konstant bleibt.
        
        df: DataFrame mit Zeitschritten als Index
        factor: int, z.B. 2 für 30-min Schritte bei 1h Originalprofil
        """
        repeated = df.loc[df.index.repeat(factor)].reset_index(drop=True)
        return repeated


    def run_timeseries_pp(self, save_at, mode, logger=None):
        """Does timeseries calculation of the pandapipes network and saves the results in save_at.

        Parameters
        ----------
        save_at : str
            Path where the results will be saved
        logger : logging.Logger, optional
            Logger instance for debugging
        
        Raises 
        ------
        Exception
            If the timeseries simulation fails
        """

        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.run_timeseries_spp")

        logger.info("=== Starting pandapipes timeseries simulation ===")

        pp_network = self.pp_network

        # Variables to log
        log_variables = [
            ("res_junction", "p_bar"),
            ("res_junction", "t_k"),
            ("res_heat_consumer", "t_from_k"),
            ("res_heat_consumer", "t_outlet_k"),
            ("res_heat_consumer", "mdot_from_kg_per_s"),
            ("res_heat_consumer", "p_from_bar"),
            ("res_heat_consumer", "p_to_bar"),
            ("res_circ_pump_pressure", "mdot_from_kg_per_s"),
            ("res_circ_pump_pressure", "t_from_k"),
            ("res_circ_pump_pressure", "deltat_k"),
            ("res_circ_pump_pressure", "qext_w"),
            ("res_circ_pump_pressure", "vdot_m3_per_s"),
            ("res_pipe", "v_mean_m_per_s"),
            ("res_pipe", "mdot_from_kg_per_s"),
            ("res_pipe", "p_from_bar"),
            ("res_pipe", "p_to_bar"),
        ]

        self.time_step = 3600 # TODO: Change in future depending on timestep input
        factor = int(3600/ self.time_step) 
        self.timesteps *= factor

        self.demand_data = self.resample_profile_constant(self.demand_data, factor)
        self.ground_temp_data = self.resample_profile_constant(self.ground_temp_data, factor)

        # --- heat-demand reading ---
        profiles_demand = self.demand_data
        for building in profiles_demand.columns:
            profiles_demand.rename(
               columns={building: list(pp_network.heat_consumer["name"]).index(building)},
                inplace=True,
            )
        profiles_demand.reset_index(drop=True, inplace=True)
        
        profiles_demand.columns = profiles_demand.columns.astype(str)
        
        profiles_demand = profiles_demand.replace(0, 1e-3)
        ds_dem = DFData(profiles_demand)

        profile_names = [str(idx) for idx in pp_network.heat_consumer.index]
        control.ConstControl(
            pp_network,
            element="heat_consumer",
            variable="qext_w",
            element_index=pp_network.heat_consumer.index.values,
            data_source=ds_dem,
            profile_name=profile_names,
        )
        
        if self.number_of_supplies > 1:
            log_variables.append(("res_circ_pump_mass", "mdot_from_kg_per_s"))
            profiles_mass_flow = profiles_demand.sum(axis=1)*self.heat_to_mass_factor
            profiles_mass_flow = pd.concat(
                [profiles_mass_flow] * (self.number_of_supplies-1), axis=1
            )
            profiles_mass_flow.columns = [
                str(idx) for idx in pp_network.circ_pump_mass.index
            ]
            ds_mass = DFData(profiles_mass_flow)

            profile_names = [str(idx) for idx in pp_network.circ_pump_mass.index]
            control.ConstControl(
                pp_network,
                element="circ_pump_mass",
                variable="mdot_flow_kg_per_s",
                element_index=pp_network.circ_pump_mass.index.values,
                data_source=ds_mass,
                profile_name=profile_names,
            )

            profile_names = [str(idx) for idx in pp_network.flow_control.index]
            control.ConstControl(
                pp_network,
                element="flow_control",
                variable="controlled_mdot_kg_per_s",
                element_index=pp_network.flow_control.index.values,
                data_source=ds_mass,
                profile_name=profile_names,
            )

        # --- ground-temperatures reading ---
        if len(self.ground_temp_data["1.0 m"]) > 1:
            profiles_t_ground = self.ground_temp_data["1.0 m"]
            logger.info(len(profiles_t_ground))
            profiles_t_ground.reset_index(drop=True, inplace=True)
            
            profiles_t_ground = pd.DataFrame(profiles_t_ground)
            profiles_t_ground.columns = ["0"]

            num_pipes = len(pp_network.pipe)
            column_names = [str(i) for i in range(num_pipes)]
            profiles_t_ground = pd.concat([profiles_t_ground["0"]] * num_pipes, axis=1)
            profiles_t_ground.columns = column_names

            ds_tground = DFData(profiles_t_ground)

            logger.info("Ground_temp")
            logger.info(profiles_t_ground)

            profile_names = [str(idx) for idx in pp_network.pipe.index]
            control.ConstControl(
                pp_network,
                element="pipe",
                variable="text_k",
                element_index=pp_network.pipe.index.values,
                data_source=ds_tground,
                profile_name=profile_names,
            )

        # --- Output configuration ---
        timesteps = range(self.timesteps)
        logger.info(timesteps)
        ow = OutputWriter(
            pp_network,
            timesteps,
            output_path=save_at,
            output_file_type=".csv",
            log_variables=log_variables,
        )

        # --- Simulation start ---
        try:
            if mode == "static":
                logger.info("Running static simulation")
                run_timeseries(pp_network, timesteps, mode="bidirectional", iter = 500)
            else:
                logger.info("Running dynamic simulation")
                run_timeseries(pp_network, timesteps, mode="bidirectional", iter = 500, transient = True, dt = self.time_step)
            logger.info("Pandapipes timeseries simulation completed successfully!")
        except Exception as e:
            logger.error(f"Timeseries simulation failed: {e}")
            raise
        
    
