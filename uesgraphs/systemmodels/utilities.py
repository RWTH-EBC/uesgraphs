"""This module collects utilities and convenience functions for model generation"""

from uesgraphs.systemmodels import systemmodelheating as sysmh
from uesgraphs.utilities import set_up_terminal_logger, set_up_file_logger

import networkx as nx
import logging
import tempfile
import os
from datetime import datetime

import pandas as pd

import warnings
from typing import Any, Dict, List, Optional, Set, Tuple


def set_up_logger(name, log_dir=None, level=int(logging.INFO)):  # Changed to INFO for more details
    """
    Set up a file-based logger with timestamp and detailed formatting.
    
    Parameters
    ----------
    name : str
        Logger name, used for log file naming
    log_dir : str, optional
        Directory for log files. If None, uses system temp directory
    level : int, optional
        Logging level (default: INFO for detailed mass flow logging)
        
    Returns
    -------
    logging.Logger
        Configured logger instance writing to timestamped file
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Determine log directory
    if log_dir is None:
        log_dir = tempfile.gettempdir()
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    print(f"Logfile findable here: {log_file}")
    
    # Configure file handler with detailed formatting
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def prepare_graph(
    graph,
    T_supply,
    p_supply,
    T_return,
    p_return,
    dT_design,
    m_flow_nominal=None,
    dp_nominal=None,
    dT_building=None,
    T_supply_building=None,
    cop_nominal=None,
    T_con_nominal=None,
    T_eva_nominal=None,
    dTEva_nominal=None,
    dTCon_nominal=None
):
    """Adds data for model generation to the uesgraph

    Parameters
    ----------
    graph : uesgraphs.uesgraph.UESGraph
        Network graph with all data for the model
    T_supply : list
        Design supply temperature in K
    p_supply : float
        Prescribed supply pressure in Pa
    T_return : float
        Design return temperature in K
    p_return : float
        Prescribed return pressure in Pa
    dT_design : float
        Design temperature difference over substation in K
    m_flow_nominal : float
        Nominal mass flow rate in kg/s
    dp_nominal : float
        Nominal pressure drop over the substation in Pa
    dT_building : float
        Prescribed temperature difference for the building heating system in K
    T_supply_building : float
        Supply temperature of the building heating system in K
    cop_nominal : float
        A nominal COP for substations that use a heat pump
    T_con_nominal : float
        Nominal condenser temperature of heat pump
    T_eva_nominal : float
        Nominal evaporator temperature of heat pump
    dTEva_nominal : float (default -10 K)
        Nominal temperature difference at heat pump evaporator
    dTCon_nominal : float (default 10 K)
        Nominal temperature difference at heat pump condenser
    """
    for node in graph.nodelist_building:
        is_supply = "is_supply_{}".format(graph.graph["network_type"])
        if graph.nodes[node][is_supply]:
            # TODO decision about variable naming
            # graph.nodes[node]['T_supply'] = T_supply
            # graph.nodes[node]['p_supply'] = [p_supply]
            # graph.nodes[node]['p_return'] = p_return
            graph.nodes[node]["TIn"] = T_supply
            graph.nodes[node]["dpIn"] = [p_supply]
            graph.nodes[node]["pReturn"] = p_return
        else:
            input_heat = graph.nodes[node]["input_heat"]
            try:
                input_dhw = graph.nodes[node]["input_dhw"]
                input_cool = graph.nodes[node]["input_cool"]
            except:
                input_dhw = [0]
                input_cool = [0]
            graph.nodes[node]["Q_flow_nominal"] = max(
                max(input_heat),
                max(input_dhw),
                max(input_cool))
            if dp_nominal is not None:
                graph.nodes[node]["dp_nominal"] = dp_nominal
            # graph.nodes[node]['dT_design'] = dT_design
            graph.nodes[node]["dTDesign"] = dT_design
            if dT_building is not None:
                # graph.nodes[node]['dT_building'] = dT_building
                graph.nodes[node]["dTBuilding"] = dT_building
            if T_supply_building is not None:
                # graph.nodes[node]['T_supply_building'] = T_supply_building
                graph.nodes[node]["TSupplyBuilding"] = T_supply_building
            if cop_nominal is not None:
                graph.nodes[node]["cop_nominal"] = cop_nominal
            if T_con_nominal is not None:
                graph.nodes[node]["T_con_nominal"] = T_con_nominal
            if T_eva_nominal is not None:
                graph.nodes[node]["T_eva_nominal"] = T_eva_nominal
            if dTEva_nominal is not None:
                graph.nodes[node]["dTEva_nominal"] = dTEva_nominal
            if dTCon_nominal is not None:
                graph.nodes[node]["dTCon_nominal"] = dTCon_nominal
        # graph.nodes[node]['T_return'] = T_return
        graph.nodes[node]["TReturn"] = T_return

    if m_flow_nominal is not None:
        for edge in graph.edges():
            graph.edges[edge[0], edge[1]]["m_flow_nominal"] = m_flow_nominal

    return graph

def create_model(
    name,
    save_at,
    graph,
    stop_time,
    timestep,
    model_supply,
    model_demand,
    model_pipe,
    model_medium,
    model_ground,
    T_nominal,
    p_nominal,
    solver=None,
    tolerance=1e-5,
    params_kusuda=None,
    fraction_glycol=None,
    pressure_control_supply=None,
    pressure_control_dp=None,
    pressure_control_building=None,
    pressure_control_p_max=None,
    pressure_control_k=None,
    pressure_control_ti=None,
    t_ground_prescribed=None,
    short_pipes_static=None,
    meta_data=None,
    logger=None
):
    """Generic model generation for setup defined through the parameters

    Parameters
    ----------
    name : str
        Name of the model (First character will be capitalized, cannot start with digit)
    save_at : str
        Directory where to store the generated model package
    graph : uesgraphs.uesgraph.UESGraph
        Network graph with all necessary data for model generation
    stop_time : int
        Stop time of the simulation in seconds
    timestep : int
        Timestep of the simulation in seconds
    model_supply : str
        One of the supply models supported by uesmodels
    model_demand : str
        One of the demand models supported by uesmodels
    model_pipe : str
        One of the pipe models supported by uesmodels
    model_medium : str
        One of the medium models supported by uesmodels
    model_ground : str
        One of the ground models supported by uesmodels
    T_nominal : float
        Nominal temperature for model initialization in K
    p_nominal : float
        Nominal pressure for model initialization in Pa
    solver : str
        Solver to use in dymola
    tolerance : float
        Solver tolerance to store in the model
    params_kusuda : dict
        Kusuda ground model parameters. Default values are for Aachen taken from TRY file
    fraction_glycol : float
        Value between 0 (100 % water) and 0.6 (60 % glycol) for the medium in the network
    pressure_control_supply : str
        Name of supply to control the pressure in the network
    pressure_control_dp : float
        Pressure difference to be held at reference building
    pressure_control_building : str
        Name of the reference building for the network. For default
        `'max_distance'`, the building with the greatest distance from the
        supply unit will be chosen
    pressure_control_p_max : float
        Maximum pressure allowed for the pressure controller
    pressure_control_k : int
        gain of controller
    pressure_control_ti : int
        time constant for integrator block
    t_ground_prescribed : list
        List of ground temperatures for every time step when using `model_ground="t_ground_table"`
    short_pipes_static : float
        The float value specifies the length of pipes considered short. If a pipe length is smaller
        than the value for `short_pipes_static`, a static pipe model will be used for it.
    meta_data : dict
        Dictionary with meta data
    logger : logging.Logger, optional
        Logger instance for debugging
    """
    # Set up logging
    if logger is None:
        logger = set_up_file_logger(f"{__name__}.create_model", level=logging.DEBUG)
    
    # Entry logging with critical parameters
    logger.info(f"=== Starting create_model for '{name}' ===")
    logger.info(f"Target directory: {save_at}")
    logger.info(f"Network type: {graph.graph.get('network_type', 'unknown')}")
    logger.debug(f"Model parameters - supply: {model_supply}, demand: {model_demand}, pipe: {model_pipe}")
    logger.debug(f"Simulation setup - stop_time: {stop_time}, timestep: {timestep}")
    
    assert not name[0].isdigit(), "Model name cannot start with a digit"

    if params_kusuda is None:
        params_kusuda = {
            "T_mean": 273.15 + 10.45,
            "T_amp": 38.5 / 2,
            "t_shift": 3,
            "alpha": 0.04,
            "D": 1,
        }
        logger.debug("Using default Kusuda parameters")

    logger.info("Creating SystemModelHeating instance")
    new_model = sysmh.SystemModelHeating(network_type=graph.graph["network_type"],logger=logger)
    new_model.stop_time = stop_time
    new_model.timestep = timestep
    
    logger.info("Importing UESGraph")
    new_model.import_from_uesgraph(graph, logger=logger)
    new_model.set_connection(remove_network_nodes=True,logger=logger)

    if solver:
        logger.debug(f"Setting solver: {solver}")
        new_model.solver = solver

    logger.debug("Configuring basic model parameters")
    new_model.add_return_network = True
    new_model.medium = model_medium
    new_model.T_nominal = T_nominal
    new_model.p_nominal = p_nominal

    if pressure_control_supply is not None:
        logger.info(f"Setting up pressure control with supply: {pressure_control_supply}")
        msg = "All or none of the pressure_control variables must be set"
        assert pressure_control_dp is not None, msg
        assert pressure_control_building is not None, msg
        assert pressure_control_p_max is not None, msg
        new_model.set_control_pressure(
            name_supply=pressure_control_supply,
            dp=pressure_control_dp,
            name_building=pressure_control_building,
            p_max=pressure_control_p_max,
            k=pressure_control_k,
            ti=pressure_control_ti
        )

    if fraction_glycol is not None:
        logger.debug(f"Setting glycol fraction: {fraction_glycol}")
        msg = "The medium model for glycol only supports fractions of glycol between 0.0 and 0.6"
        assert fraction_glycol >= 0 and fraction_glycol <= 0.6, msg
        new_model.fraction_glycol = fraction_glycol

    if model_ground == "t_ground_table":
        logger.debug("Using t_ground_table for ground model")
        new_model.ground_model = "t_ground_table"
    elif model_ground == "t_ground_kusuda":
        logger.debug("Using t_ground_kusuda for ground model")
        new_model.ground_model = "t_ground_kusuda"
        new_model.params_kusuda = params_kusuda

    if t_ground_prescribed is not None:
        logger.debug(f"Setting prescribed ground temperatures (length: {len(t_ground_prescribed)})")
        new_model.graph["T_ground"] = t_ground_prescribed

    new_model.tolerance = tolerance

    # ===== CRITICAL SECTION: comp_model assignment =====
    logger.info("=== Starting comp_model assignment for buildings ===")
    logger.debug(f"Building nodes count: {len(new_model.nodelist_building)}")
    logger.debug(f"model_supply for assignment: '{model_supply}'")
    logger.debug(f"model_demand for assignment: '{model_demand}'")
    
    for node in new_model.nodelist_building:
        is_supply = "is_supply_{}".format(new_model.network_type)
        is_supply_value = new_model.nodes[node][is_supply]
        
        logger.debug(f"Processing building node '{node}': {is_supply}={is_supply_value}")
        
        if is_supply_value:
            logger.debug(f"  -> Assigning SUPPLY model: '{model_supply}'")
            new_model.nodes[node]["comp_model"] = model_supply
        else:
            logger.debug(f"  -> Assigning DEMAND model: '{model_demand}'")
            new_model.nodes[node]["comp_model"] = model_demand
        
        # Validate assignment
        assigned_value = new_model.nodes[node]["comp_model"]
        logger.debug(f"  SUCCESS: comp_model assigned: '{assigned_value}'")
        
        # Check if assignment looks like a template path (potential problem!)
        if assigned_value and ('\\' in assigned_value or '/' in assigned_value):
            logger.warning(f"  WARNING: comp_model looks like a path, not a model name: '{assigned_value}'")

    # Pipe model assignment
    logger.info("=== Starting comp_model assignment for pipes ===")
    logger.debug(f"Pipe nodes count: {len(new_model.nodelist_pipe)}")
    logger.debug(f"model_pipe for assignment: '{model_pipe}'")
    
    for node in new_model.nodelist_pipe:
        logger.debug(f"Processing pipe node '{node}'")
        new_model.nodes[node]["comp_model"] = model_pipe
        
        if short_pipes_static is not None:
            length = new_model.nodes[node]["length"]
            logger.debug(f"  Pipe length: {length}, short_pipes_static threshold: {short_pipes_static}")
            if length < short_pipes_static:
                static_model = "AixLib.Fluid.DistrictHeatingCooling.Pipes.StaticPipe"
                logger.debug(f"  -> Using static pipe model: '{static_model}'")
                new_model.nodes[node]["comp_model"] = static_model

    # Final model setup
    name = name[0].upper() + name[1:]
    logger.info(f"Setting final model name: '{name}'")
    new_model.model_name = name
    new_model.meta_data = meta_data
    
    logger.info(f"Writing Modelica package to: {save_at}")
    new_model.write_modelica_package(save_at=save_at)
    
    logger.info(f"=== create_model completed successfully for '{name}' ===")

    # Save the model to JSON for later use
    json_path = save_system_model_to_json(new_model, save_at + "/model.json")
    print(f"Model JSON saved at {json_path}")

    return new_model


def save_system_model_to_json(model, filepath):
    """
    Save a SystemModelHeating object to a JSON file with comprehensive attribute capturing.
    
    Parameters:
        model: SystemModelHeating - The model to save
        filepath: str - Path where the JSON file should be saved
    
    Returns:
        str - Path to the saved file
    """
    import json
    # Create a dictionary to store all model data
    model_data = {
        # Store class information
        "class_info": {
            "type": model.__class__.__name__,
            "module": model.__class__.__module__
        },
        
        # Constructor parameters (only these will be used for initialization)
        "init_params": {
            "model_name": getattr(model, "model_name", "Test"),
            "network_type": getattr(model, "network_type", "heating")
        },
        
        # Store all other attributes separately
        "attributes": {},
        
        # Store graph structure
        "graph": {
            "nodes": [],
            "edges": []
        }
    }
    
    # Save all instance attributes (excluding built-in attributes)
    for attr_name in dir(model):
        # Skip private attributes, methods, and constructor parameters
        if (attr_name.startswith('_') or callable(getattr(model, attr_name)) or 
            attr_name in model_data["init_params"]):
            continue
            
        try:
            attr_value = getattr(model, attr_name)
            # Try to make it JSON serializable
            try:
                json.dumps(attr_value)
                model_data["attributes"][attr_name] = attr_value
            except (TypeError, OverflowError):
                # If not serializable, convert to string representation
                model_data["attributes"][attr_name] = str(attr_value)
        except Exception as e:
            # Skip attributes that cannot be accessed or serialized
            print(f"Skipping attribute {attr_name}: {e}")
    
    # Save all node data
    for node in model.nodes():
        node_data = {
            "id": node,
            "attributes": {}
        }
        
        # Copy all serializable attributes
        for key, value in model.nodes[node].items():
            if key == "position" and hasattr(value, "x") and hasattr(value, "y"):
                # Special handling for shapely Point objects
                node_data["attributes"]["position"] = {
                    "x": value.x,
                    "y": value.y
                }
            else:
                # Try to make the value JSON serializable
                try:
                    json.dumps(value)
                    node_data["attributes"][key] = value
                except (TypeError, OverflowError):
                    # If not serializable, convert to string
                    node_data["attributes"][key] = str(value)
        
        model_data["graph"]["nodes"].append(node_data)
    
    # Save all edge data
    for u, v in model.edges():
        edge_data = {
            "source": u,
            "target": v,
            "attributes": {}
        }
        
        # Copy all serializable attributes
        for key, value in model.edges[u, v].items():
            try:
                json.dumps(value)
                edge_data["attributes"][key] = value
            except (TypeError, OverflowError):
                edge_data["attributes"][key] = str(value)
        
        model_data["graph"]["edges"].append(edge_data)
    
    # Save to file with pretty printing for readability
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(model_data, f, indent=2)
    
    print(f"Model saved to {filepath}")
    return filepath


def load_system_model_from_json(filepath):
    """
    Load a SystemModelHeating object from a JSON file, respecting the constructor's signature.
    
    Parameters:
        filepath: str - Path to the JSON file
    
    Returns:
        SystemModelHeating - The reconstructed model
    """
    # Import required modules
    import importlib
    import json
    import shapely.geometry as sg
    
    # Load the JSON data
    with open(filepath, 'r', encoding='utf-8') as f:
        model_data = json.load(f)
    
    # Get the class information
    class_info = model_data.get("class_info", {})
    class_name = class_info.get("type", "UESGraph")
    module_name = class_info.get("module", "uesgraphs.uesgraph")
    
    try:
        # Dynamically import the module and get the class
        module = importlib.import_module(module_name)
        ModelClass = getattr(module, class_name)
        
        # Get only the initialization parameters
        init_params = model_data.get("init_params", {})
        
        # Create a new instance with only the constructor parameters
        model = ModelClass(**init_params)
        
        # Set all other attributes manually after initialization
        for attr_name, attr_value in model_data.get("attributes", {}).items():
            try:
                setattr(model, attr_name, attr_value)
            except Exception as e:
                print(f"Warning: Could not set attribute {attr_name}: {e}")
        
    except (ImportError, AttributeError) as e:
        # Fallback to UESGraph if the specific class can't be imported
        print(f"Warning: Could not create {class_name} ({e}). Creating UESGraph instead.")
        model = UESGraph()
    
    # Add nodes with all attributes
    for node_data in model_data["graph"]["nodes"]:
        node_id = node_data["id"]
        
        # Add the node to the graph
        model.add_node(node_id)
        
        # Set node attributes
        for key, value in node_data["attributes"].items():
            if key == "position" and isinstance(value, dict) and "x" in value and "y" in value:
                # Reconstruct shapely Point objects
                model.nodes[node_id][key] = sg.Point(value["x"], value["y"])
            else:
                model.nodes[node_id][key] = value
    
    # Add edges with all attributes
    for edge_data in model_data["graph"]["edges"]:
        source = edge_data["source"]
        target = edge_data["target"]
        
        # Add the edge to the graph
        model.add_edge(source, target)
        
        # Set edge attributes
        for key, value in edge_data["attributes"].items():
            model.edges[source, target][key] = value
    
    print(f"Model loaded from {filepath}")
    return model
 

def estimate_fac(graph, u_form_distance=25, n_gate_valve=2.0):
    """Calculate fac for all pipes based on m_flow_nominal

    Parameters
    ----------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    u_form_distance : int
        distance between U-form for thermal stress of pipes. Default: every 25m one U-Form is added
    n_gate_valve : float
        number of gate valves per pipe. For average values, n_gate_valve is a float. Default: 2 Gate valves per pipe.
    Returns
    -------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    """

    for edge in graph.edges():
        d = graph.edges[edge]["diameter"]
        l = graph.edges[edge]["length"]

        # guess equivalent length
        # Data taken from https://neutrium.net/fluid_flow/pressure-loss-from-fittings-equivalent-length-method/

        # Approx. every 25 m a U-form for thermal pressure is installed
        # U-form equals four 90° elbow fittings
        l_thermal_U_form = round(l / u_form_distance, 0) * 20 * 4

        # Every pipe is connected at both ends with a tee run-through
        l_tee_junction = 2 * 20

        # Every pipe has n_gate_valve Gate valves installed
        l_gate_valve = n_gate_valve * 8

        l_eq = l_thermal_U_form + l_tee_junction + l_gate_valve
        # factor accounts for theoretical additional length because of pressure drop by fittings
        fac = 1 + l_eq * d / l

        graph.edges[edge]["fac"] = fac

    return graph

def estimate_m_flow_nominal(graph, dT_design, network_type, cp=4184):
    """
    DEPRECATED: Use estimate_m_flow_demand_based instead.
    
    This function is maintained for backward compatibility and will be
    removed in version X.Y.Z.
    
    Calculate all design mass flows based on nominal loads for each edge.
    
    Parameters
    ----------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    dT_design : float
        Design temperature difference between supply and return in K
    network_type : str
        {'heating', 'cooling'}
    cp : float
        Specific heat capacity of fluid in the network
        
    Returns
    -------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    """
    warnings.warn(
        "Function estimate_m_flow_nominal is deprecated and will be removed in "
        "future versions. Use estimate_m_flow_demand_based instead.",
        DeprecationWarning, 
        stacklevel=2
    )
    
    # Set the same dT value for all nodes
    for node in graph.nodes():
        graph.nodes[node]['dT_Network'] = dT_design
    
    # Call the new function with appropriate parameters
    return estimate_m_flow_demand_based(
        graph=graph,
        network_type=network_type,
        cp=cp,
        dT_attribute='dT_Network',
        load_scenario='peak_load'  # Assume nominal = peak load
    )


def estimate_m_flow_nominal_tablebased(graph, network_type):
    """Calculate m_flow_nominal based on the pipe diameter.

    This function calculates the m_flow_nominal based on the pipe diameter
    and according to the isoplus table for suggested m_flows for specific pipe
    diameters with a average pressure loss of 70 Pa/m. Link: 
    http://www.isoplus.de/fileadmin/user_upload/downloads/documents/germany/Catalogue_German/Kapitel_2_Starre_Verbundsysteme.pdf
    page 9

    Parameters
    ----------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    network_type : str
        {'heating', 'cooling'}

    Returns
    -------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    """
    # As this function wants to estimate the nominal massflow based on the diameter,
    # the key is the diameter, the value is the nominal massflow
    # {
    #  key: value,
    #  diameter [mm]: m_flow_nominal [kg/s]
    # }
    pipe_dict = {
        21.7: 0.125,
        27.3: 0.25,
        36: 0.513888889,
        41.9: 0.763888889,
        53.9: 1.416666667,
        69.7: 2.819444444,
        82.5: 4.305555556,
        107.1: 8.541666667,
        132.5: 15,
        160.3: 24.58333333,
        210.1: 50,
        263: 90,
        312.7: 141.5277778,
        344.4: 182.6388889,
        393.8: 258.6111111,
        444.6: 354.1666667,
        495.4: 470.8333333,
        595.8: 755.5555556,
        695: 1130.555556,
        795.4: 1615.277778,
        894: 2347.222222,
        994: 2555.555556,
    }

    # min(enumerate(a), key=lambda x: abs(x[1]-11.5))

    for edge in graph.edges():
        diameter = graph.edges[edge]["diameter"]
        m_flow_nominal = pipe_dict[
            min(pipe_dict, key=lambda x: abs(x - diameter * 1000))
        ]
        graph.edges[edge[0], edge[1]]["m_flow_nominal"] = m_flow_nominal

    return graph




def size_hydronic_network(
    graph: Any,
    m_flow_key = None,
    catalog = None,
    dT_attribute: str = "dT_Network",
    network_type: str = "heating",
    demand_attribute: str = "input_heat",
    load_scenario: str = "peak_load",
    cp: float = 4184,
    logger: Optional[logging.Logger] = None
) -> Any:
    
    # Set up logger
    if logger is None:
        logger = set_up_logger(
            name="hydronic_network_sizing",
            #log_dir="./logs",  # Optional: specify custom directory
            level=logging.DEBUG  # INFO level captures all important steps
        )

    if m_flow_key == None:
        # Estimate mass flows
        logger.info(f"Sizing hydronic network: estimating mass flows for {network_type} network with {load_scenario} scenario")
        graph = estimate_m_flow_demand_based(
            graph=graph,
            network_type=network_type,
            demand_attribute=demand_attribute,
            load_scenario=load_scenario,
            cp=cp,
            dT_attribute=dT_attribute,
            logger=logger  
        )
        m_flow_key = f"m_flow_{load_scenario}"

    logger.info("Mass flow estimation completed successfully")
    
    # Estimate pipe diameters
    logger.info(f"Sizing hydronic network: estimating pipe diameters for {network_type} network with {load_scenario} scenario")
    if catalog:
        df = load_pipe_catalog(catalog)
        get_pipe_catalog_DN_m_flow(graph,pipe_catalog=df,logger=logger, mass_flow_key=m_flow_key, dn_key="DN", diameter_key="diameter", robust=True)
    else:
        raise NotImplementedError()
    
    return graph



def estimate_m_flow_demand_based(
    graph: Any,
    network_type: str = "heating",
    demand_attribute: str = "input_heat",
    load_scenario: str = "peak_load",
    cp: float = 4184,
    dT_attribute: str = "dT_Network",
    logger: Optional[logging.Logger] = None
) -> Any:
    """
    Estimates mass flow for each edge by calculating flows at demand nodes and propagating backwards.
    
    This function implements a physically correct approach where mass flows are calculated
    at each demand node based on their specific load and temperature difference, then
    aggregated backwards through the network following mass conservation principles.
    
    Parameters
    ----------
    graph : UESGraph or nx.Graph
        The graph representing the network with nodelist_building attribute.
    network_type : str, optional
        Type of network, default is "heating". Must be "heating" or "cooling".
    demand_attribute : str, optional
        Attribute name containing load values in demand nodes, default is "input_heat".
    load_scenario : str, optional
        Load scenario for calculation, default is "peak_load".
        Options: "peak_load" (maximum value) or "average_load" (mean value).
    cp : float, optional
        Specific heat capacity of the fluid in J/(kg*K), default is 4184.
    dT_attribute : str
        Node attribute name for temperature difference values in Kelvin.
        Must be present in all demand nodes with positive numeric values.
        Used for individual mass flow calculations at each demand node.
    logger : logging.Logger, optional
        Logger instance for logging messages. If None, creates a default logger.
        
    Returns
    -------
    graph : UESGraph or nx.Graph
        Input graph with additional edge attributes:
        - m_flow_{load_scenario}: Mass flow rate in kg/s for each edge
        - contributing_demands_{load_scenario}: List of demand nodes contributing to edge flow
        - supply_attribution_{load_scenario}: Dictionary showing which supply serves which demands
        
    Raises
    ------
    TypeError
        If graph does not have required nodelist_building attribute.
    ValueError
        If network_type or load_scenario parameters are invalid.
        If no supply or demand nodes are found.
        If required node attributes are missing.
    """
    # Initialize logger
    if logger is None:
        logger = set_up_logger(
            name="",
            #log_dir="./logs",  # Optional: specify custom directory
            level=logging.DEBUG  # INFO level captures all important steps
        )    
    # Validate input parameters
    _validate_parameters(graph, network_type, load_scenario, demand_attribute)
    
    # Step 1: Identify and categorize nodes
    supply_nodes, demand_nodes = _identify_network_nodes(
        graph, network_type, demand_attribute, logger
    )
    
    # Step 2: Calculate mass flows at demand nodes
    demand_mass_flows = _calculate_demand_mass_flows(
        graph, demand_nodes, demand_attribute, load_scenario, cp, dT_attribute, logger
    )
    
    # Step 3: Build supply-to-demand flow paths
    supply_demand_paths = build_flow_paths(
        graph, supply_nodes, demand_nodes, logger
    )
    
   # Step 4: Aggregate mass flows on edges using maximum principle
    _aggregate_edge_flows_robust(
        graph, supply_demand_paths, demand_mass_flows, load_scenario, logger
    )
    
    logger.info(f"Successfully calculated mass flows for {len(graph.edges)} edges "
               f"using demand-based approach with {load_scenario} scenario")
    
    return graph


def _validate_parameters(
    graph: Any, 
    network_type: str, 
    load_scenario: str, 
    demand_attribute: str
) -> None:
    """Validate input parameters for the mass flow estimation function."""
    if not hasattr(graph, "nodelist_building"):
        raise TypeError("Graph must be a UESGraph object with nodelist_building attribute")
    
    if network_type not in ["heating", "cooling"]:
        raise ValueError("network_type must be 'heating' or 'cooling'")
    
    if load_scenario not in ["peak_load", "average_load"]:
        raise ValueError("load_scenario must be 'peak_load' or 'average_load'")


def _identify_network_nodes(
    graph: Any, 
    network_type: str, 
    demand_attribute: str, 
    logger: logging.Logger
) -> Tuple[List[Any], List[Any]]:
    """
    Identify and categorize supply and demand nodes in the network.
    
    Returns
    -------
    tuple
        (supply_nodes, demand_nodes) - Lists of supply and demand node identifiers
    """
    supply_nodes = []
    demand_nodes = []
    supply_attr = f"is_supply_{network_type}"
    
    for node in graph.nodelist_building:
        # Check for required supply attribute
        if supply_attr not in graph.nodes[node]:
            raise ValueError(f"Node {node} missing required attribute '{supply_attr}'")
        
        if graph.nodes[node][supply_attr]:
            supply_nodes.append(node)
        else:
            # Validate demand node has required load attribute
            if demand_attribute not in graph.nodes[node]:
                raise ValueError(f"Demand node {node} missing required attribute '{demand_attribute}'")
            demand_nodes.append(node)
    
    # Ensure we have both supply and demand nodes
    if not supply_nodes:
        raise ValueError(f"No supply nodes found for network type '{network_type}'")
    if not demand_nodes:
        raise ValueError(f"No demand nodes found for network type '{network_type}'")
    
    logger.info(f"Identified {len(supply_nodes)} supply nodes and {len(demand_nodes)} demand nodes")
    return supply_nodes, demand_nodes


def _calculate_demand_mass_flows(
    graph: Any,
    demand_nodes: List[Any],
    demand_attribute: str,
    load_scenario: str,
    cp: float,
    dT_attribute: str,
    logger: logging.Logger
) -> Dict[Any, float]:
    """
    Calculate mass flow requirements at each demand node.
    
    This function processes each demand node individually, calculating the required
    mass flow based on the node's load and temperature difference (dT).
    
    Parameters
    ----------
    graph : UESGraph or nx.Graph
        Network graph containing node data
    demand_nodes : List[Any]
        List of demand node identifiers
    demand_attribute : str
        Attribute name containing load values
    load_scenario : str
        Either "peak_load" or "average_load"
    cp : float
        Specific heat capacity in J/(kg*K)
    dT_attribute : str
        Node attribute name for temperature difference values in Kelvin.
        Must be present in all demand nodes with positive numeric values.
        Used for individual mass flow calculations at each demand node.
    logger : logging.Logger
        Logger for status messages
        
    Returns
    -------
    Dict[Any, float]
        Dictionary mapping demand node identifiers to their mass flow requirements in kg/s
    """
    
    for demand_node in demand_nodes:
        if dT_attribute not in graph.nodes[demand_node]:
            # Get available attributes for better error message
            available_attrs = list(graph.nodes[demand_node].keys())
            dT_related_attrs = [attr for attr in available_attrs if 'dT' in attr or 'delta' in attr.lower() or 'temp' in attr.lower()]

            error_msg = (
                f"Demand node '{demand_node}' is missing the required temperature difference attribute '{dT_attribute}'. "
                f"This attribute must contain the temperature difference (dT) in Kelvin between supply and return flow "
                f"for mass flow calculation (formula: m_flow = thermal_load / (cp * dT)).\n\n"
                f"To fix this issue:\n"
                f"1. Add '{dT_attribute}' attribute to node '{demand_node}' with a numeric value in Kelvin\n, like with graph.nodes[{demand_node}]['{dT_attribute}'] = 30\n"
                f"2. Or specify a different attribute name using the 'dT_attribute' parameter\n"
            )

            if dT_related_attrs:
                error_msg += f"\nConsider using: dT_attribute='{dT_related_attrs[0]}' if appropriate, when calling method"

            raise ValueError(error_msg)
        
    demand_mass_flows = {}
    
    for demand_node in demand_nodes:
        # Extract load values from node attribute
        load_values = graph.nodes[demand_node][demand_attribute]
        
        # Handle both single values and lists
        if isinstance(load_values, (int, float)):
            load_values = [load_values]
        
        # Convert to absolute values for calculation
        abs_load_values = [abs(x) for x in load_values]
        
        # Calculate load based on scenario
        if load_scenario == "peak_load":
            load = max(abs_load_values)
        elif load_scenario == "average_load":
            load = sum(abs_load_values) / len(abs_load_values)
        
        # Get node-specific temperature difference
        node_dT = graph.nodes[demand_node][dT_attribute]
        # Validate dT value
        if not isinstance(node_dT, (int, float)) or node_dT <= 0:
            raise ValueError(
                f"Temperature difference (dT) for demand node '{demand_node}' must be a positive number, "
                f"got {node_dT} (type: {type(node_dT).__name__})"
            )

        # Calculate mass flow: m_flow = Q / (cp * dT)
        mass_flow = load / (cp * node_dT)
        demand_mass_flows[demand_node] = mass_flow
        
        logger.debug(f"Demand node {demand_node}: load={load:.2f}W, dT={node_dT}K, "
                    f"m_flow={mass_flow:.6f}kg/s")
    
    
    total_demand_flow = sum(demand_mass_flows.values())
    logger.info(f"Calculated mass flows for {len(demand_nodes)} demand nodes, "
               f"total demand: {total_demand_flow:.6f} kg/s")
    
    return demand_mass_flows

def build_flow_paths(
    graph: Any,
    supply_nodes: List[Any],
    demand_nodes: List[Any],
    logger: logging.Logger
) -> Dict[Tuple[Any, Any], List[Tuple[Any, Any]]]:
    """
    Build flow paths from each supply node to reachable demand nodes.
    
    This function identifies all supply-demand pairs that are connected and
    determines the shortest path between them, converting paths to edge lists.
    
    Parameters
    ----------
    graph : UESGraph or nx.Graph
        Network graph
    supply_nodes : List[Any]
        List of supply node identifiers
    demand_nodes : List[Any]
        List of demand node identifiers
    logger : logging.Logger
        Logger for status messages
        
    Returns
    -------
    Dict[Tuple[Any, Any], List[Tuple[Any, Any]]]
        Dictionary mapping (supply, demand) tuples to lists of edges in the flow path
    """
    supply_demand_paths = {}
    unreachable_demands = set(demand_nodes)  # Track which demands are reachable
    
    for supply in supply_nodes:
        reachable_from_this_supply = []
        
        for demand in demand_nodes:
            try:
                if nx.has_path(graph, supply, demand):
                    # Calculate shortest path and convert to edge list
                    node_path = nx.shortest_path(graph, supply, demand)
                    edge_path = [(node_path[i], node_path[i + 1]) 
                                for i in range(len(node_path) - 1)]
                    
                    supply_demand_paths[(supply, demand)] = edge_path
                    reachable_from_this_supply.append(demand)
                    
                    # Remove from unreachable set
                    unreachable_demands.discard(demand)
                    
            except nx.NetworkXNoPath:
                # Explicitly handle case where no path exists
                continue
        
        logger.debug(f"Supply {supply} can reach {len(reachable_from_this_supply)} demands: "
                    f"{reachable_from_this_supply}")
    
    # Log summary information
    total_paths = len(supply_demand_paths)
    logger.info(f"Built {total_paths} supply-to-demand flow paths")
    
    if unreachable_demands:
        logger.warning(f"Unreachable demand nodes found: {list(unreachable_demands)}")
    
    return supply_demand_paths

def _aggregate_edge_flows_robust(
    graph: Any,
    supply_demand_paths: Dict[Tuple[Any, Any], List[Tuple[Any, Any]]],
    demand_mass_flows: Dict[Any, float],
    load_scenario: str,
    logger: logging.Logger
) -> None:
    """
    Aggregate mass flows on edges using a robust supply-based approach with maximum flow principle.
    
    This function implements a two-stage aggregation process:
    1. For each supply node, calculate cumulative flows on all edges serving its connected demands
    2. Apply maximum flow principle when multiple supplies can serve the same edge
    
    This approach ensures robust network sizing where each edge is dimensioned for the worst-case
    scenario among all possible supply configurations.
    
    Parameters
    ----------
    graph : UESGraph or nx.Graph
        Network graph to be modified with calculated flow data
    supply_demand_paths : Dict[Tuple[Any, Any], List[Tuple[Any, Any]]]
        Mapping of (supply, demand) pairs to their corresponding edge paths
    demand_mass_flows : Dict[Any, float]
        Mass flow requirements for each demand node in kg/s
    load_scenario : str
        Load scenario identifier used for attribute naming in the graph
    logger : logging.Logger
        Logger instance for progress and summary information
    """
    logger.info("Starting robust edge flow aggregation using supply-based approach")
    
    # Initialize data structures for supply-based flow tracking
    supply_edge_flows = {}  # {supply_node: {edge: accumulated_flow}}
    edge_contributing_demands = {}  # {edge: set_of_demand_nodes}
    supply_attribution = {}  # {demand_node: supply_node}
    
    # Step 1: Group supply-demand paths by supply node for separate processing
    supplies = set(supply for supply, demand in supply_demand_paths.keys())
    logger.info(f"Processing flows for {len(supplies)} supply nodes")
    
    # Step 2: Calculate aggregated flows for each supply node independently
    for supply in supplies:
        supply_edge_flows[supply] = {}
        demands_served = []
        
        logger.debug(f"Processing supply node: {supply}")
        
        # Process all demand nodes served by this supply
        for (sup, demand), edge_path in supply_demand_paths.items():
            if sup == supply:
                demand_flow = demand_mass_flows[demand]
                demands_served.append(demand)
                
                # Record supply attribution for this demand
                supply_attribution[demand] = supply
                
                # Accumulate demand flow along the entire path to this demand
                for edge in edge_path:
                    # Add flow to supply-specific edge flow tracking
                    if edge in supply_edge_flows[supply]:
                        supply_edge_flows[supply][edge] += demand_flow
                    else:
                        supply_edge_flows[supply][edge] = demand_flow
                    
                    # Track which demands contribute to each edge for documentation
                    if edge not in edge_contributing_demands:
                        edge_contributing_demands[edge] = set()
                    edge_contributing_demands[edge].add(demand)
        
        total_supply_flow = sum(demand_mass_flows[d] for d in demands_served)
        logger.debug(f"Supply {supply}: serves {len(demands_served)} demands, "
                    f"total flow = {total_supply_flow:.6f} kg/s")
    
    logger.debug(f"Identified flows: {supply_edge_flows}")

    # Step 3: Apply maximum flow principle across all supplies for robust sizing
    logger.info("Applying maximum flow principle across supplies for robust edge sizing")
    final_edge_flows = {}
    supply_conflicts = {}  # Track edges with multiple supply options
    
    for supply, edge_flows in supply_edge_flows.items():
        for edge, flow in edge_flows.items():
            # Normalize edge representation for consistent dictionary access
            normalized_edge = __normalize_edge(edge)
            logger.debug(f"Processing edge {edge} with flow {flow:.6f} kg/s from supply {supply}")
            if normalized_edge  in final_edge_flows:
                # Multiple supplies can serve this edge - apply maximum principle
                if normalized_edge  not in supply_conflicts:
                    supply_conflicts[normalized_edge ] = []
                supply_conflicts[normalized_edge ].append((supply, flow))
                
                # Update to maximum flow value for robust design
                final_edge_flows[normalized_edge ] = max(final_edge_flows[normalized_edge ], flow)
            else:
                # First supply to use this edge
                final_edge_flows[normalized_edge ] = flow
    
    # Log information about supply conflicts and robust sizing decisions
    if supply_conflicts:
        logger.info(f"Applied maximum flow principle to {len(supply_conflicts)} edges "
                   f"with multiple supply options")
        for edge, conflicts in supply_conflicts.items():
            flows = [f"{supply}: {flow:.6f}" for supply, flow in conflicts]
            max_flow = final_edge_flows[edge]
            logger.debug(f"Edge {edge} - Supplies: [{', '.join(flows)}] -> "
                        f"Selected: {max_flow:.6f} kg/s")
    
    # Step 4: Apply calculated flows to all graph edges
    edges_with_flow = 0
    edges_without_flow = 0
    
    for edge in graph.edges:
        # Normalize the current graph edge for dictionary lookup
        normalized_edge = __normalize_edge(edge)
        if normalized_edge in final_edge_flows:
            # Set mass flow attribute for edges with calculated flows
            graph.edges[normalized_edge][f"m_flow_{load_scenario}"] = final_edge_flows[normalized_edge]
            #graph.edges[normalized_edge][f"contributing_demands_{load_scenario}"] = list(edge_contributing_demands[normalized_edge]) lists contain non normalized edges
            
            edges_with_flow += 1
        else:
            logger.warning(f"Edge {edge} has no flow assigned, setting to 0.0 kg/s")
            # Initialize edges without flow (not part of any supply-demand path)
            graph.edges[normalized_edge][f"m_flow_{load_scenario}"] = 0.0
            graph.edges[normalized_edge][f"contributing_demands_{load_scenario}"] = []
            edges_without_flow += 1
    
    # Step 5: Store supply attribution information at graph level for reference
    graph.graph[f"supply_attribution_{load_scenario}"] = supply_attribution
    
    # Step 6: Calculate and log comprehensive summary statistics
    total_demand_flow = sum(demand_mass_flows.values())
    active_edges_flow = sum(final_edge_flows.values()) if final_edge_flows else 0.0
    
    logger.info(f"Flow aggregation completed successfully:")
    logger.info(f"  - Total demand flow: {total_demand_flow:.6f} kg/s")
    logger.info(f"  - Edges with flow: {edges_with_flow}/{len(graph.edges)}")
    logger.info(f"  - Edges without flow: {edges_without_flow}")
    logger.info(f"  - Supply-demand pairs processed: {len(supply_demand_paths)}")
    
    # Log flow distribution statistics for active edges
    if final_edge_flows:
        max_edge_flow = max(final_edge_flows.values())
        min_edge_flow = min(final_edge_flows.values())
        avg_edge_flow = sum(final_edge_flows.values()) / len(final_edge_flows)
        
        logger.info(f"Active edge flow statistics:")
        logger.info(f"  - Maximum edge flow: {max_edge_flow:.6f} kg/s")
        logger.info(f"  - Minimum edge flow: {min_edge_flow:.6f} kg/s")
        logger.info(f"  - Average edge flow: {avg_edge_flow:.6f} kg/s")
    
    logger.info("Robust edge flow aggregation completed successfully")

def __normalize_edge(edge):
    """
    Normalize edge tuple to consistent order for undirected graph operations.
    
    This function ensures that edges (A, B) and (B, A) are treated as the same edge
    by always returning the tuple with the smaller node ID first.
    
    Args:
        edge (tuple): Edge as (node1, node2)
        
    Returns:
        tuple: Normalized edge as (min_node, max_node)
    """
    return tuple(sorted(edge))



def get_pipe_catalog_DN_m_flow(
    graph,
    pipe_catalog: pd.DataFrame,
    logger: logging.Logger,
    mass_flow_key: str,
    dn_key: str,
    diameter_key: str,
    robust: bool = True
) -> None:
    """
    Assign pipe diameters to edges based on mass flow and catalog data.
    
    Parameters
    ----------
    graph : Graph
        Network graph with edges containing mass flow data
    pipe_catalog : pd.DataFrame
        Catalog with columns: DN, inner_diameter, mass_flow_min, mass_flow_max
    logger : logging.Logger
        Logger instance
    mass_flow_key : str
        Edge attribute containing mass flow [kg/s]
    dn_key : str
        Edge attribute to store DN (default: "DN")
    diameter_key : str
        Edge attribute to store diameter [m] (default: "diameter")
    robust : bool
        If True, selects next larger pipe when no exact match (default: True)
    """
    # Collect all edges missing the required mass flow attribute
    missing_edges = []
    for edge in graph.edges:
        if mass_flow_key not in graph.edges[edge]:
            missing_edges.append(edge)

    if missing_edges:
        logger.error("The following edges are missing the '%s' attribute:", mass_flow_key)
        for edge in missing_edges:
            logger.error("  - %s", edge)
        raise ValueError(
            f"Aborting because edges are missing the '{mass_flow_key}' attribute."
        )

    # Update DN and the diameter information for each edge
    for edge in graph.edges:
        m_flow = graph.edges[edge][mass_flow_key]
        matching_rows = pipe_catalog[
            (pipe_catalog['mass_flow_min'] <= m_flow) &
            (pipe_catalog['mass_flow_max'] >= m_flow)
        ]
        num_matches = len(matching_rows)

        # Scenario 1: No matching row
        if num_matches == 0:
            if robust:
                # Attempt to find the next bigger pipe
                bigger_rows = pipe_catalog[pipe_catalog['mass_flow_min'] > m_flow]
                if not bigger_rows.empty:
                    logger.warning(
                        "Edge %s: No row directly matches mass_flow=%.2f. "
                        "Using the next bigger pipe.",
                        edge, m_flow
                    )
                    next_bigger_idx = bigger_rows['mass_flow_min'].idxmin()
                    chosen_row = bigger_rows.loc[next_bigger_idx]
                else:
                    # Fallback: there is no bigger pipe either
                    raise ValueError(
                        f"Edge {edge}: No direct match for flow {m_flow}, "
                        "and no bigger pipe available. Consider extending your pipe catalog."
                    )
            else:
                raise ValueError(
                    f"Edge {edge}: No matching row for flow {m_flow}, and robust=False. "
                    "Consider adding more pipe entries or adjusting your data."
                )

        # Scenario 2: Exactly one match
        elif num_matches == 1:
            chosen_row = matching_rows.iloc[0]

        # Scenario 3: Multiple matching rows
        else:
            if robust:
                logger.warning(
                    "Edge %s: Multiple matching rows for mass_flow=%.2f. "
                    "Selecting the row with the largest DN among them.",
                    edge, m_flow
                )
                max_dn_idx = matching_rows['DN'].idxmax()
                chosen_row = matching_rows.loc[max_dn_idx]
            else:
                raise ValueError(
                    f"Edge {edge}: Multiple rows match flow {m_flow}, robust=False. "
                    "Validate pipe catalog ranges for overlaps or remove duplicates."
                )

        dn_value = chosen_row['DN']
        diameter_value = float(chosen_row['inner_diameter'])

        if dn_key in graph.edges[edge]:
            logger.warning(
                "Edge %s already has '%s' set to %s and will be overwritten.",
                edge, dn_key, graph.edges[edge][dn_key]
            )
        if diameter_key in graph.edges[edge]:
            logger.warning(
                "Edge %s already has '%s' set to %s and will be overwritten.",
                edge, diameter_key, graph.edges[edge][diameter_key]
            )

        graph.edges[edge][dn_key] = dn_value
        graph.edges[edge][diameter_key] = diameter_value

        logger.info(
            "Edge %s updated: %s=%s, %s=%.2f (mass_flow=%.2f)",
            edge, dn_key, dn_value, diameter_key, diameter_value, m_flow
        )


def load_pipe_catalog(catalog_name: str = "isoplus",custom_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load pipe catalog data from CSV file in the data/pipe_catalogs directory.
    
    This function loads manufacturer pipe catalog data containing pipe dimensions
    and flow capacities for different nominal diameters (DN). The catalog files
    are expected to be located in the data/pipe_catalogs subdirectory relative
    to the systemmodels module.
    
    Parameters
    ---------- 
    catalog_name : str, optional
        Name of the pipe catalog to load (default: "isoplus")
        The function will look for a file named "{catalog_name}.csv"
        
    Returns
    -------
    pd.DataFrame
        DataFrame containing pipe catalog data with columns:
        - DN: Nominal diameter [designated, e.g. DN20]
        - wall_thickness: Pipe wall thickness [m] 
        - inner_diameter: Inner pipe diameter [m]
        - mass_flow_min: Minimum mass flow capacity [kg/s]
        - mass_flow_max: Maximum mass flow capacity [kg/s]
        
    Raises
    ------
    FileNotFoundError
        If the specified catalog file does not exist
    ValueError
        If the catalog file exists but contains invalid data structure
        
    Examples
    --------
    >>> catalog = load_pipe_catalog("isoplus")
    >>> print(catalog.columns.tolist())
    ['DN', 'wall_thickness', 'inner_diameter', 'mass_flow_min', 'mass_flow_max']
    
    >>> # Load different catalog (if available)
    >>> rehau_catalog = load_pipe_catalog("rehau")
    
    Notes
    -----
    The CSV files can contain comment lines starting with '#' which will be
    automatically ignored during loading. This allows for metadata and source
    information to be stored directly in the catalog files.
    
    The function expects the catalog files to be located at:
    {module_directory}/uesgraphs/data/pipe_catalogs/{catalog_name}.csv
    """
    
    if custom_path:
        catalog_path = os.path.join(custom_path, f"{catalog_name}.csv")
    else:
        # Einfacher relativer Pfad
        current_dir = os.path.dirname(os.path.abspath(__file__))
        catalog_path = os.path.join(current_dir, "..", "data", "pipe_catalogs", f"{catalog_name}.csv")
    
    # Convert to absolute path for better error reporting
    catalog_path = os.path.abspath(catalog_path)    

    if not os.path.exists(catalog_path):
        raise FileNotFoundError(f"Catalog '{catalog_name}' not found at: {catalog_path}")
    
    try:
        # Load CSV data, ignoring comment lines starting with '#'
        catalog_df = pd.read_csv(catalog_path, comment='#')
        
        # Validate required columns exist
        required_columns = ['DN', 'inner_diameter', 'mass_flow_min', 'mass_flow_max']
        missing_columns = [col for col in required_columns if col not in catalog_df.columns]
        
        if missing_columns:
            raise ValueError(
                f"Catalog '{catalog_name}' is missing required columns: {missing_columns}\n"
                f"Available columns: {catalog_df.columns.tolist()}"
            )
        
        # Sort by DN for consistent ordering
        catalog_df = catalog_df.sort_values('inner_diameter').reset_index(drop=True)
        
        return catalog_df
        
    except pd.errors.EmptyDataError:
        raise ValueError(f"Catalog file '{catalog_name}' is empty or contains no valid data")
    except pd.errors.ParserError as e:
        raise ValueError(f"Error parsing catalog file '{catalog_name}': {str(e)}")



