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
        timesteps,
        network_type="heating",
        logger=None
    ):
        
        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.__init__")
        logger.info(f"=== Initializing SystemModelHeating ===")

        super(SystemModelHeating, self).__init__()

        self.time_step = timesteps
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
        for node in uesgraph_input.nodes:
            try:
                node_data = uesgraph_input.nodes[node]
                pos = node_data["position"]

                # Supply-node (heating)
                if node_data["node_type"] == "building" and node_data.get("is_supply_heating", False):
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
            - pipe_nodes: Mapping of pipe indices to uesgraph edges
        """

        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.import_pipes_from_uesgraph")
            
        logger.info("=== Starting pipe import from UESGraph ===")
        pipe_list = []
        pipe_nodes = {}
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
                        alpha_w_per_m2k=heat_trans,
                        sections=edge_data["sections"],
                        text_k=T_ground,
                        name=f"{pipe_type}_{uesgraph_input.edges[edge]['diameter']}_{uesgraph_input.edges[edge]['pipeID']}"
                    )
                    pipe_list.append({"index": pipe_index, "from": from_node, "to": to_node, "type": pipe_type})
                    pipe_index += 1
                
                self.pipe_map_supply[pipe] = edge
                self.pipe_map_return[pipe] = edge

            except KeyError as e:
                logger.error(f"Key error for edge {edge}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error for edge {edge}: {e}")

        return pipe_list, pipe_nodes

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
            - pipe_nodes: Mapping of pipe indices to uesgraph edges
            - heat_source_id: ID of the heat source junction
            - heat_source_r_id: ID of the heat source return junction
        """

        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.import_from_uesgraph")
        
        logger.info("=== Starting full UESGraph import (pandapipes) ===")

        # Step 1: Junctions
        junction_ids, heat_source_id, heat_source_r_id = self.import_nodes_from_uesgraph(
            uesgraph_input, logger=logger
        )

        # Step 2: Pipes
        pipe_list, pipe_nodes = self.import_edges_from_uesgraph(
            uesgraph_input, junction_ids, logger=logger
        )

        data = {}
        max_len = 0

        for node in uesgraph_input.nodes:
            node_data = uesgraph_input.nodes[node]
            # only take buildings
            if node_data.get("node_type") != "building" or node_data.get("is_supply_heating", False):
                continue
            heat = node_data.get("input_heat", [])
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
        return junction_ids, pipe_list, pipe_nodes, heat_source_id, heat_source_r_id
    
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

    def run_timeseries_spp(self, save_at, logger=None):
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
        ]

        # --- heat-demand reading ---
        profiles_demand = self.demand_data
        logger.info(len(profiles_demand))
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
            run_timeseries(pp_network, timesteps, mode="sequential")
            logger.info("Pandapipes timeseries simulation completed successfully!")
        except Exception as e:
            logger.error(f"Timeseries simulation failed: {e}")
            raise

    
    def assign_csv_data_to_uesgraph(self, uesgraph_input, base_folder, logger=None):
        """
        Reads CSV-pandapipes results (Junctions & Pipes)
        and saves them as Pandas Series in UESGraph.

        base_folder must have these folders:
        - res_junction/
        - res_pipe/

        Files and the names in the graph:
        res_junction/p_bar.csv       → pressure
        res_junction/t_k.csv         → temperature
        res_pipe/mdot_from_kg_per_s.csv → mflow
        res_pipe/v_mean_m_per_s.csv      → velocity

        Parameters
        ----------
        uesgraph_input : uesgraphs.uesgraph.UESGraph object
            UESGraph to assign the data to
        base_folder : str
            Folder where the CSV results are stored
        logger : logging.Logger, optional
            Logger instance for debugging
        
        Returns
        -------
        uesgraphs.uesgraph.UESGraph object
            UESGraph with assigned data
        """

        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.SystemModelHeating.assign_csv_data_to_uesgraph")

        base_folder = Path(base_folder)

        # Mappings depend on supply_type
        junction_map, pipe_map = self.get_current_mappings(uesgraph_input)

        logger.info(junction_map)
        logger.info(pipe_map)

        # CSV --> Variable Name Mapping
        csv_to_var = {
            "p_bar": "pressure",
            "t_k": "temperature",
            "mdot_from_kg_per_s": "mflow",
            "v_mean_m_per_s": "velocity"
        }

        # --- Junction-Data -----------------------------------------------------
        junction_folder = base_folder / "res_junction"
        for fname, var_name in [("p_bar.csv", "pressure"), ("t_k.csv", "temperature")]:
            fpath = junction_folder / fname
            if not fpath.exists():
                continue
            
            df = pd.read_csv(fpath, index_col=0, sep=';')
            if var_name == "pressure":
                df = df*100000

            for col in df.columns:
                col_idx = int(col)
                if col_idx in junction_map:
                    node_id = junction_map[col_idx]
                    uesgraph_input.nodes[node_id][var_name] = df[col].tolist()  # Pandas Series

        # --- Pipe-Data ---------------------------------------------------------
        pipe_folder = base_folder / "res_pipe"
        for fname, var_name in [("mdot_from_kg_per_s.csv", "m_flow"),
                                ("v_mean_m_per_s.csv", "velocity")]:
            fpath = pipe_folder / fname
            if not fpath.exists():
                continue

            df = pd.read_csv(fpath, index_col=0, sep=';')

            for col in df.columns:
                col_idx = int(col)
                if col_idx in pipe_map:
                    edge = pipe_map[col_idx]
                    uesgraph_input.edges[edge][var_name] = df[col].tolist()  # Pandas Series

        return uesgraph_input

    def get_current_mappings(self, graph):
        """Returns the current junction and pipe mappings based on supply_type.
        Parameters
        ----------
        graph : uesgraphs.uesgraph.UESGraph object
            UESGraph to check the supply_type from
        Returns
        -------
        Tuple[dict, dict]
            Tuple containing junction_map and pipe_map
        """

        supply_type = graph.graph.get("supply_type", "supply")

        if supply_type == "supply":
            return (self.junction_map_supply, self.pipe_map_supply)

        else:
            return (self.junction_map_return, self.pipe_map_return)
        
    
