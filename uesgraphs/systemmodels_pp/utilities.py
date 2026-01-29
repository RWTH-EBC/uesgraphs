# heating_pipeline.py
from uesgraphs.uesgraph import UESGraph
from uesgraphs.systemmodels_pp import systemmodelheating as spp 
from uesgraphs.utilities import set_up_file_logger, set_up_terminal_logger 
import pandas as pd

import logging
import tempfile
import pickle
import os
from datetime import datetime
import warnings
from pathlib import Path

from typing import Optional



def set_up_file_logger(name: str, log_dir: Optional[str] = None, level: int = logging.ERROR) -> logging.Logger:
    """
    Set up a full file+console logger for major functions.

    Args:
        name: Logger name
        log_dir: Directory for log files (default: temp directory)
        level: Logging level (default: ERROR)

    Returns:
        Configured file+console logger
    """
    logger = logging.getLogger(name)

   # if logger.handlers:
    #    return logger

    logger.setLevel(level)
    if log_dir is None:
        log_dir = tempfile.gettempdir()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{name}{timestamp}.log")
    print(f"Logfile findable here: {log_file}")

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger


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


def assign_csv_data_to_uesgraph(uesgraph_input, base_folder, mappings, logger=None):
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
    supply_type = uesgraph_input.graph.get("supply_type", "supply")

    logger.info(supply_type)

    junction_map = mappings[supply_type]["junction"]
    pipe_map = mappings[supply_type]["pipe"]

    logger.info(junction_map)
    # CSV --> Variable Name Mapping
    csv_to_var = {
        "p_bar": "pressure",
        "t_k": "temperature",
        "mdot_from_kg_per_s": "mflow",
        "v_mean_m_per_s": "velocity",
        "p_from_bar": "pressure_from",
        "p_to_bar": "pressure_to"
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

    p_in = None
    # --- Pipe-Data ---------------------------------------------------------
    pipe_folder = base_folder / "res_pipe"
    for fname, var_name in [("mdot_from_kg_per_s.csv", "m_flow"),
                                ("p_from_bar.csv", "pressure_from"),
                                ("p_to_bar.csv", "pressure_to")]:
        fpath = pipe_folder / fname
        if not fpath.exists():
            continue

        df = pd.read_csv(fpath, index_col=0, sep=';')
        if var_name == "pressure_from":
            df = df*100000
            p_in = df
            continue
        elif var_name == "pressure_to":
            df = df*100000
            if p_in is not None:
                df = p_in - df
                var_name = "dp"
            else:
                df = df

        for col in df.columns:
            col_idx = int(col)
            if col_idx in pipe_map:
                edge = pipe_map[col_idx]
                uesgraph_input.edges[edge][var_name] = df[col].tolist()  # Pandas Series

    return uesgraph_input

### Main Function for creating the model ###

def create_model(
    name,
    save_at,
    graph,
    stop_time,
    timestep,
    mode,
    t_ground_prescribed=None,
    logger=None
):
    """Generic model generation for setup defined through the parameters

    Parameters
    ----------
    name : str
        Name of the model (First character will be capitalized, cannot start with digit)
    save_at : str
        Directory where to store the generated model results
    graph : uesgraphs.uesgraph.UESGraph
        Network graph with all necessary data for model generation
    stop_time : int
        Stop time of the simulation in seconds
    timestep : int
        Timestep of the simulation in seconds
    t_ground_prescribed : list
        List of ground temperatures for every time step
    logger : logging.Logger, optional
        Logger instance for debugging

    Returns
    -------
    new_model : spp.SystemModelHeating
        Generated system model
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network with assigned simulation results
    """
    # Set up logging
    if logger is None:
        logger = set_up_file_logger(f"{__name__}.create_model", level=logging.DEBUG)
    
    # Entry logging with critical parameters
    logger.info(f"=== Starting create_model for '{name}' ===")
    logger.info(f"Target directory: {save_at}")
    logger.info(f"Network type: {graph.graph.get('network_type', 'unknown')}")
    logger.debug(f"Simulation setup - stop_time: {stop_time}, timestep: {timestep}")
    
    assert not name[0].isdigit(), "Model name cannot start with a digit"

    assert mode in ("static","dynamic"), "Mode must be either 'static' or 'dynamic'"

    logger.info("Creating SystemModelHeating instance")
    new_model = spp.SystemModelHeating(stop_time = stop_time, timestep = timestep, network_type=graph.graph["network_type"],logger=logger)
    
    logger.info("Importing UESGraph")
    _, pipe_list, heat_source_ids, heat_source_r_ids = new_model.import_from_uesgraph(graph, logger=logger)

    if t_ground_prescribed is not None:
        logger.debug(f"Setting prescribed ground temperatures (length: {len(t_ground_prescribed)})")
        new_model.graph["T_ground"] = t_ground_prescribed
        new_model.ground_temp_data = pd.DataFrame(
            {"1.0 m": new_model.graph["T_ground"]}
        )
    
    #mode = "static"

    if mode != "dynamic":
        new_model.run_timeseries_spp(save_at, mode, logger=logger)
    else:
        new_model.run_timeseries_dpp(pipe_list, heat_source_ids, heat_source_r_ids, save_at, logger=logger)

    mappings = {
        "supply": {
            "junction": new_model.junction_map_supply,
            "pipe": new_model.pipe_map_supply,
        },
        "return": {
            "junction": new_model.junction_map_return,
            "pipe": new_model.pipe_map_return,
        },
    }

    with open(Path(save_at) / "mappings.pkl", "wb") as f:
        pickle.dump(mappings, f)

    graph = assign_csv_data_to_uesgraph(graph, save_at, mappings, logger=logger)

    logger.info(f"=== create_model completed successfully for '{name}' ===")
    return new_model, graph

def uesgraph_to_pandapipes(uesgraph, simplification_level,
                         workspace,
                         sim_setup_path,
                         input_heating, input_dhw, input_cooling,
                         ground_temp_path,
                         logger=None,
                         log_level=logging.DEBUG
                         ):
    """
    Convert an Urban Energy System Graph (UESGraph) to pandapipes model and simulate it.

    This function processes a UESGraph, applies simplification, adds demand data,
    and generates the pandapipes results based on simulation parameters.

    Parameters:
    -----------
    uesgraph : UESGraph object or str
        The UESGraph object or path to a JSON file containing the UESGraph data
    simplification_level : int
        Level of simplification to apply to the UESGraph (higher = more simplified)
    workspace : str or Path
        Directory path where output files will be saved
    sim_setup_path : str or Path
        Path to the simulation setup configuration file
    input_heating : str or Path
        Path to heating demand data
    input_dhw : str or Path
        Path to domestic hot water demand data
    input_cooling : str or Path
        Path to cooling demand data
    ground_temp_path : str or Path
        Path to ground temperature data file
    logger : logging.Logger, optional
        Logger instance. If None, creates a new file logger in temp directory
    log_level : int, optional
        Logging level (default is logging.DEBUG). Only used if logger is None

    Returns:
    --------
    None

    Raises:
    -------
    FileNotFoundError: If required files are missing
    ValueError: If uesgraph parameter is invalid
    Exception: For various processing errors with detailed messages
    """
    # Set up logging configuration
    if logger is None:
        logger = set_up_file_logger("pandapipesSim", level=int(log_level))

    # Step 0: Resolve all paths to absolute paths (prevents issues with os.chdir in to_json)
    logger.debug("Resolving all input paths to absolute paths")
    workspace = os.path.abspath(str(workspace))
    sim_setup_path = os.path.abspath(str(sim_setup_path))
    input_heating = os.path.abspath(str(input_heating))
    input_dhw = os.path.abspath(str(input_dhw))
    input_cooling = os.path.abspath(str(input_cooling))
    ground_temp_path = os.path.abspath(str(ground_temp_path))

    logger.debug(f"Resolved workspace: {workspace}")
    logger.debug(f"Resolved sim_setup_path: {sim_setup_path}")
    logger.debug(f"Resolved ground_temp_path: {ground_temp_path}")

    # Step 1: Validate input files and folders
    logger.info("Validating files")
    paths_to_check = [sim_setup_path, input_heating, input_dhw, input_cooling, ground_temp_path]
    existing_files, missing_files = validate_paths(paths_to_check)
    if missing_files:
        logger.error(f"Missing files: {missing_files}")
        raise FileNotFoundError("Some files are missing. Please check the logs for details.")
    logger.debug(f"Existing files: {existing_files}")

    # Step 2: Load simulation configuration from Excel
    logger.info("Loading simulation settings from Excel")
    sim_params = load_simulation_settings_from_excel(sim_setup_path, logger)
    logger.debug(f"Simulation settings loaded: {sim_params}")

    # Step 3: Initialize or load the UESGraph from file or object
    logger.info("Initialize UESGraph")

    if isinstance(uesgraph, (str, os.PathLike, Path)):
        if str(uesgraph).endswith(".json"):
            try:
                uesgraph_path = str(uesgraph)
                uesgraph = UESGraph()
                uesgraph.from_json(path = uesgraph_path, network_type="heating")
                logger.info(f"UESGraph loaded from JSON: {uesgraph_path}")
            except Exception as e:
                raise Exception(f"While loading UESGraph from JSON: {e}")
        else:
            raise ValueError(f"Value for uesgraph: {uesgraph} is nor uesgraph object nor valid JSON path")
    elif isinstance(uesgraph, UESGraph):
        # Normalize UESGraph via JSON
        logger.info("Normalize UESGraph via JSON")
        name = "uesgraphs_origin"
        origin_path = Path(workspace) / f"{name}.json"

        try:
            # Save to JSON
            uesgraph.to_json(
                path=str(workspace),
                name=name,
                all_data=True,
                prettyprint=True
            )
            logger.info(f"Original UESGraph saved to {origin_path}")

            # Reload from JSON to normalize internal structures
            normalized_graph = UESGraph()
            normalized_graph.from_json(
                path=str(origin_path),
                network_type="heating"
            )

            # Replace with normalized version
            uesgraph = normalized_graph
            logger.info("UESGraph normalized successfully")

        except Exception as e:
            logger.error(f"Failed to normalize UESGraph: {e}")
            raise
    else:
        raise ValueError(f"uesgraph must be either a JSON path or UESGraph object, got: {type(uesgraph)}")

    logger.info("Writing network_type to UESGraph")
    uesgraph.graph["network_type"] = "heating"

    # Step 3.1: Ensure all edges have names (required for pandapipes simulation model)
    # This is needed because from_geojson() doesn't set edge names automatically,
    # while from_json() does (via pipeID). We need consistent behavior.
    logger.info("Validating and generating edge names if needed")
    edges_without_names = 0
    edges_total = uesgraph.number_of_edges()

    for edge in uesgraph.edges():
        if 'name' not in uesgraph.edges[edge]:
            # Generate name from connected node names
            node_0_name = uesgraph.nodes[edge[0]].get('name', edge[0])
            node_1_name = uesgraph.nodes[edge[1]].get('name', edge[1])
            edge_name = f"{node_0_name}_{node_1_name}"
            uesgraph.edges[edge]['name'] = edge_name
            edges_without_names += 1
            logger.debug(f"Generated name for edge {edge}: '{edge_name}'")

    if edges_without_names > 0:
        logger.info(f"Generated names for {edges_without_names}/{edges_total} edges that were missing names")
    else:
        logger.info(f"All {edges_total} edges already have names")

    try:
        # Step 4: Assign demand data to the graph nodes
        logger.info("Assigning demand data")
        input_paths_dict = {
            "heating": input_heating,
            "cooling": input_cooling,
            "dhw": input_dhw
        }
        uesgraph, msg = assign_demand_data(uesgraph, input_paths_dict)
        logger.debug(msg)

        # Step 4.1: Save the UESGraph with added demand data
        logger.info("Try to save uesgraph with demand data")
        try:
            uesgraph.to_json(path=str(workspace),
                        name = "transurban_seestadt_uesgraphs_with_demand",
                        all_data = True,
                        prettyprint = True)
            logger.info("UESGraph with demand data saved")
        except Exception as e:
            logger.error(f"Failed to save uesgraph with demand data: {e}")

        # Step 5: Assign pipe parameters from Excel
        logger.info("*** Assigning pipe parameters from Excel ***")
        try:
            excel_params = _load_excel(sim_setup_path, 'Pipes', logger)
            for edge in uesgraph.edges():
                uesgraph.edges[edge]["dIns"] = excel_params.get("dIns", 0.038)
                uesgraph.edges[edge]["kIns"] = excel_params.get("kIns", 0.035)
                uesgraph.edges[edge]["roughness"] = excel_params.get("roughness", 0.000025)*1000
                uesgraph.edges[edge]["ground_depth"] = excel_params.get("ground_depth", 1)
                uesgraph.edges[edge]["sections"] = excel_params.get("sections", 5)
            logger.info("Pipe parameters successfully assigned")
        except Exception as e:
            logger.error(f"Failed to assign pipe parameters: {e}")
            raise

        # Step 6: Assign supply parameters from Excel
        logger.info("*** Assigning supply parameters from Excel ***")
        supplies = 0
        try:
            excel_params = _load_excel(sim_setup_path, 'Supply', logger)
            for node in uesgraph.nodelist_building:
                is_supply = "is_supply_{}".format(uesgraph.graph["network_type"])
                if uesgraph.nodes[node][is_supply]:
                    uesgraph.nodes[node]["TIn"] = excel_params.get("TIn", 324)
                    uesgraph.nodes[node]["TReturn"] = excel_params.get("TReturn", 290)
                    uesgraph.nodes[node]["dpIn"] = excel_params.get("pIn", 500000)/100000  # Convert from Pa to bar
                    uesgraph.nodes[node]["pReturn"] = excel_params.get("pReturn", 200000)/100000
                    uesgraph.nodes[node]["dpFlow"] = excel_params.get("dpFlow", 300000)/100000
                    supplies += 1
            logger.info("Supply parameters successfully assigned")
        except Exception as e:
            logger.error(f"Failed to assign supply parameters: {e}")
            raise
        uesgraph.graph["number_of_supplies"] = supplies
        # Step 7: Assign demand parameters from Excel
        logger.info("*** Assigning demand parameters from Excel ***")
        try:
            excel_params = _load_excel(sim_setup_path, 'Demands', logger)
            uesgraph.graph["dT_Net"]= excel_params.get("dT_Network", 25)
            uesgraph.graph["cp_default"] = excel_params.get("cp_default", 4180)  
            for node in uesgraph.nodelist_building:
                is_supply = "is_supply_{}".format(uesgraph.graph["network_type"])
                if not uesgraph.nodes[node][is_supply]:
                    uesgraph.nodes[node]["dTDesign"] = excel_params.get("dT_Network", 25)
                    uesgraph.nodes[node]["TReturn"] = excel_params.get("TReturn", 290)
                    uesgraph.nodes[node]["cp_default"] = excel_params.get("cp_default", 4180)
            logger.info("Demand parameters successfully assigned")
        except Exception as e:
            logger.error(f"Failed to assign demand parameters: {e}")
            raise 
        # Step 8: Load ground temperature data for simulations
        logger.info("Loading ground temperature data")
        ground_temp_df = load_ground_temp_data(ground_temp_path)
        logger.debug(f"Ground temperature data loaded of shape: {ground_temp_df.shape}")

        # Step 9: Simplify the UESGraph according to the specified level
        logger.info(f"*** Start simplyfing Uesgraph with simplification level: {simplification_level} ***")
        #logger.info(f"Before simplification: {len(uesgraph.edges())} edges with total length {uesgraph.calc_network_length(network_type='heating')}")
        #uesgraph = simplify_uesgraph(uesgraph, simplification_level)
        #logger.info(f"After simplification: {len(uesgraph.edges())} edges with total length {uesgraph.calc_network_length(network_type='heating')}")

        # Step 9.1: Save the simplified UESGraph
        logger.info("Try to save uesgraph after simplification")
        try:
            uesgraph.to_json(path=str(workspace),
                        name = "uesgraphs_simplified",
                        all_data = True,
                        prettyprint = True)
            logger.info("UESGraph after simplification saved")
        except Exception as e:
            logger.error(f"Failed to save uesgraph after simplification: {e}")

        # Step 10: Create directory structure for Pandapipes output files
        logger.info("Creating subfolder for pandapipes files")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sim_name = f"Sim{timestamp}"
        sim_model_dir = os.path.join(workspace, "models", sim_name)
        os.makedirs(sim_model_dir, exist_ok=True)
        logger.info(f"Pandapipes files will be saved to: {sim_model_dir}")

        # Step 11: Generate pandapipes simulation using Excel-based simulation parameters
        logger.info("Start process for pandapipes simulation using Excel parameters")
        sim_name_ix = f"{sim_name}_{str(sim_params['simulation_name'])}"
        logger.info(f"Processing simulation: {sim_params['simulation_name']}")

        # Extract ground temperature data (assuming ground_depth is in sim_params or use default)
        ground_depth = sim_params.get('ground_depth', '1.0 m')  # Default fallback
        ground_temp_list = ground_temp_df[ground_depth].tolist()
        logger.info(f"Using ground temperature data for depth {ground_depth}")

        # Save simulation parameters to CSV if requested
        if sim_params.get("save_params_to_csv", False):
            logger.info("Saving simulation parameters to CSV")
            save_setup_params_to_csv(sim_params, sim_name_ix, sim_model_dir)

        try:
            logger.info(f"Start creating model for simulation: {sim_name_ix}")
            graph = generate_simulation_model(
                uesgraph=uesgraph,
                sim_name=sim_name_ix,
                sim_params=sim_params,
                ground_temp_list=ground_temp_list,
                sim_model_dir=sim_model_dir,
                logger=logger
            )
            try:
                graph.to_json(path=str(workspace),
                            name = "uesgraphs",
                            all_data = True,
                            prettyprint = True)
                graph.to_json(path=str(sim_model_dir),
                            name = "uesgraphs",
                            all_data = True,
                            prettyprint = True)
                logger.info("UESGraph after simulation saved")
            except Exception as e:
                logger.error(f"Failed to save uesgraph after simulation: {e}")
        except Exception as e:
            logger.error(f"Error while generating pandapipes simulation: {e}")
            raise e

    except Exception as e:
        logger.error(f"Error while processing uesgraph: {e}")
        raise e
    
### Helper functions ###

def load_simulation_settings_from_excel(excel_path, logger=None):
    """
    Load simulation settings from Excel 'Simulation' sheet.

    Parameters
    ----------
    excel_path : str or Path
        Path to Excel file containing simulation settings
    logger : logging.Logger, optional
        Logger instance

    Returns
    -------
    sim_params : dict
        Dictionary of simulation parameters

    Raises
    ------
    ValueError
        If required simulation parameters are missing
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.load_simulation_settings_from_excel")

    sim_params = _load_excel(excel_path, 'Simulation', logger)

    # Validate required simulation parameters
    required = ['simulation_name', 'start_time', 'stop_time', 'mode']
    missing = [param for param in required if param not in sim_params]

    if missing:
        raise ValueError(f"Missing required simulation parameters in 'Simulation' sheet: {missing}")

    logger.info(f"Simulation settings loaded from Excel: {sim_params.get('simulation_name')}")
    return sim_params

def _load_excel(excel_path, excel_sheet_name, logger):
    """
    Load parameters from Excel file.
    
    Parameters
    ----------
    excel_path : str or Path or None
        Path to Excel file (optional)
    excel_sheet_name : str
        Name of the Excel sheet to load
    logger : logging.Logger
        Logger instance
        
    Returns
    -------
    excel_params : dict
        Dictionary of parameters from Excel (empty dict if excel_path is None)
    """
    excel_params = {}
    
    if excel_path is not None:
        try:
            logger.info(f"Loading parameters from Excel: {excel_path}")
            excel_params = load_component_parameters(excel_path, excel_sheet_name)
            logger.debug(f"Excel parameters loaded: {list(excel_params.keys())}")
        except Exception as e:
            warning_msg = f"Could not load Excel parameters: {e}"
            logger.warning(warning_msg)
            warnings.warn(warning_msg, UserWarning)
    else:
        logger.info("No Excel file provided, using only graph attributes")
    
    return excel_params

def load_component_parameters(excel_path, component_type):
    """
    Load component parameters from an Excel file.
    
    Reads a specific sheet from an Excel file and returns parameters as a dictionary.
    Expected Excel structure:
    - Column A: Parameter (parameter names)
    - Column B: Value (parameter values)
    
    Parameters
    ----------
    excel_path : str or Path
        Path to the Excel file containing component parameters
    component_type : str
        Type of component, must be one of: 'pipes', 'supply', 'demands', 'simulation'
        This determines which sheet to read from the Excel file
        
    Returns
    -------
    dict
        Dictionary with parameter names as keys and their values
        Returns empty dict if sheet not found
        
    Raises
    ------
    FileNotFoundError
        If the Excel file does not exist
    ValueError
        If the component_type is not valid or Excel structure is incorrect
        
    Examples
    --------
    >>> params = load_component_parameters('parameters.xlsx', 'pipes')
    >>> print(params['dp_nominal'])
    0.10
    """
    # Validate component type
    valid_types = ['Pipes', 'Supply', 'Demands', 'Simulation']
    if component_type not in valid_types:
        raise ValueError(
            f"Invalid component_type '{component_type}'. "
            f"Must be one of: {', '.join(valid_types)}"
        )
    
    # Check if file exists
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found: {excel_path}")
    
    try:
        # Read the specific sheet
        df = pd.read_excel(excel_path, sheet_name=component_type)
        
        # Validate Excel structure
        if len(df.columns) < 2:
            raise ValueError(
                f"Excel sheet '{component_type}' must have at least 2 columns "
                "(Parameter and Value)"
            )
        
        # Check if first row contains expected column names
        if 'Parameter' not in df.columns and 'parameter' not in df.columns.str.lower():
            # Assume first two columns are Parameter and Value
            df.columns = ['Parameter', 'Value'] + list(df.columns[2:])
        
        # Create dictionary from Parameter and Value columns
        # Drop rows where Parameter is NaN
        df_clean = df[['Parameter', 'Value']].dropna(subset=['Parameter'])

        # Convert to dictionary
        param_dict = dict(zip(df_clean['Parameter'], df_clean['Value']))

        # Convert and clean values
        import math
        for key, value in param_dict.items():
            # Convert NaN to None
            if isinstance(value, float) and math.isnan(value):
                param_dict[key] = None
            # Try to convert string values to appropriate types
            elif isinstance(value, str):
                value_stripped = value.strip()

                # Skip if it looks like a reference (@something) or template path/name
                if value_stripped.startswith('@') or '/' in value_stripped or '.' in value_stripped and not value_stripped.replace('.', '').replace('e', '').replace('E', '').replace('-', '').replace('+', '').isdigit():
                    continue

                # Try boolean conversion
                if value_stripped.upper() in ('TRUE', 'FALSE'):
                    param_dict[key] = value_stripped.upper() == 'TRUE'
                # Try numeric conversion (handles scientific notation like '1e5')
                else:
                    try:
                        # Try float first (handles both '123' and '1.23' and '1e5')
                        param_dict[key] = float(value_stripped)
                    except ValueError:
                        # Keep as string if conversion fails (e.g., template names)
                        pass

        return param_dict
        
    except ValueError as e:
        if "Worksheet named" in str(e):
            # Sheet doesn't exist
            logging.warning(
                f"Sheet '{component_type}' not found in {excel_path}. "
                f"Returning empty dictionary."
            )
            return {}
        else:
            raise
    
    except Exception as e:
        raise Exception(
            f"Error reading Excel file {excel_path}, sheet '{component_type}': {e}"
        )

def generate_simulation_model(uesgraph, sim_name, sim_params, ground_temp_list, sim_model_dir, logger=None):
    """
    Generate pandapipes simulation model using Excel-based parameter system.

    This function assumes parameters are already assigned to uesgraph nodes/edges
    via the assign_*_parameters functions.

    Parameters
    ----------
    uesgraph : UESGraph
        Graph with pre-assigned parameters from Excel
    sim_name : str
        Name of the simulation
    sim_params : dict
        Simulation parameters from Excel 'Simulation' sheet
    ground_temp_list : list
        Ground temperature data
    sim_model_dir : str
        Directory to save pandapipes files
    logger : logging.Logger, optional
        Logger instance
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.generate_simulation_model")

    logger.info("Setting up UESGraph for pandapipes simulation")

    # Ensure node names are strings
    for node in list(uesgraph.nodes()):
        uesgraph.nodes[node]["name"] = str(uesgraph.nodes[node]["name"])

    # Set network type
    uesgraph.graph["network_type"] = "heating"
  

    # Create system model
    logger.info("Creating system model with pre-assigned parameters")

    _, graph = create_model(
        name=sim_name,
        save_at=sim_model_dir,
        graph=uesgraph,
        stop_time=float(sim_params["stop_time"]),
        timestep=sim_params.get("timestep",3600),  # Could be made configurable
        mode=sim_params.get("mode", "static"),
        t_ground_prescribed=ground_temp_list
    )

    logger.info(f"pandapipes Model generated: {sim_name}")

    return graph 

### Process demand data and assign to uesgraph

def assign_demand_data(uesgraph, input_paths_dict, input_types = ["heating", "cooling", "dhw"],demand_mode = 0):
    """
    Assigns energy demand data to buildings in a UES (Urban Energy Systems) graph.
    
    This function reads demand profiles from CSV files and assigns them to building nodes
    in the graph. For buildings without specific demand data, it uses a fallback profile
    (dummy demand) based on the first building in the respective CSV file. The function
    can handle heating, cooling, and domestic hot water (DHW) demands.

    Parameters
    ----------
    uesgraph : ueesgraphs Graph
        The urban energy system graph containing building nodes.
    input_paths_dict : dict
        Dictionary containing file paths for each demand type.
        Expected keys: 'heating', 'cooling', 'dhw'.
    input_types : list, optional
        List of demand types to process. Default is ["heating", "cooling", "dhw"].
    demand_mode : int, optional
        Mode for demand calculation. Currently only mode 0 is implemented,
        which combines heating and DHW demands for peak load calculation.

    Returns
    -------
    tuple
        - Updated UES graph with demand data assigned to building nodes
        - Message string containing information about the data assignment process
        
    Notes
    -----
    Building nodes are updated with the following attributes:
        - input_heat: List of heating demand values
        - input_cool: List of cooling demand values
        - input_dhw: List of DHW demand values
        - max_demand_heating: Maximum combined heating/DHW demand
    
    The function handles missing data by:
        1. Using a dummy profile if a building is not found in demand data
        2. Tracking which buildings exist in CSVs but not in the graph
    """

    msg = "Following Messages occured while loading demand data: \n"

    #Define empty dictionaries for demand data
    dict_inputs = {}
    dummy_demand = {}

    try:
        for input_type in input_types:
            df = pd.read_csv(input_paths_dict[input_type],
                            parse_dates=True,
                            index_col=0)
            dict_inputs[input_type] = df.rename(columns=lambda x: x.lower())
            
            #Store dummy demand (first data column) for missing buildings
            dummy_demand[input_type] = df[df.columns[1]].tolist()
    except FileNotFoundError as e:
        print(f"Failed to load demand data: {e}")

    missing_bldgs = dict_inputs["heating"].columns.to_list()

    #Process each building
    for bldg_node in uesgraph.nodelist_building:
        if uesgraph.nodes[bldg_node]["is_supply_heating"]:
            continue

        bldg_name = uesgraph.nodes[bldg_node]["name"]
        demands = {}

        #Get damand profiles for each type, ues dummy if missing
        for input_type in input_types:
            try:
                demands[input_type] = dict_inputs[input_type][bldg_name].tolist()
                if input_type == "heating":
                    missing_bldgs.remove(bldg_name)
            except KeyError:
                demands[input_type] = dummy_demand[input_type]
                msg += f"Building {bldg_name} not found in {input_type} data. Using dummy demand."

        #Save demands to node
        node = uesgraph.nodes[bldg_node]
        node.update({
            "input_dhw": demands["dhw"],
            "input_heat": demands["heating"],
            "input_cool": demands["cooling"]
        })
    if len(missing_bldgs)>0:
        msg += f"Missing buildings: {missing_bldgs}"
    else:
        msg += "No missing buildings found."

    return uesgraph, msg
    
### Administrative Helper functions ###

def validate_paths(paths):
    """
    Validate if the provided file and directory paths exist.
    
    Parameters:
    -----------
    paths : list
        List of paths (strings or Path objects) to validate
        
    Returns:
    --------
    tuple
        (existing_paths, missing_paths): Two lists containing the paths that exist
        and the paths that are missing, respectively
    """
    existing_paths = []
    missing_paths = []
    
    # Check each path and categorize as existing or missing
    for path in paths:
        path_str = str(path)
        if os.path.exists(path_str):
            existing_paths.append(path_str)
        else:
            missing_paths.append(path_str)
            
    return existing_paths, missing_paths

def load_ground_temp_data(ground_temp_path):
    try:
        ground_temp = pd.read_csv(ground_temp_path,
                                  parse_dates=True,
                                  index_col=0)
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {ground_temp_path}")
    if len(ground_temp.index) == 0:
        raise ValueError("CSV file is empty")
    
    
    return ground_temp

def save_setup_params_to_csv(setup_params, sim_name, sim_model_dir):
    """
    Save simulation setup parameters to a CSV file.
    
    This function takes a single row from the simulation setup Excel file (as a dictionary)
    and saves it as a CSV file in a specified directory, with parameters as rows and their 
    values as a single column.
    
    Parameters:
    -----------
    setup_params : dict
        Dictionary containing simulation setup parameters (a single row from the Excel setup)
    sim_name : str
        Name of the current simulation, used for filename generation
    sim_model_dir : str
        Directory where to save the CSV file
        
    Returns:
    --------
    str
        Path to the saved CSV file
    """
    # Ensure the target directory exists
    os.makedirs(sim_model_dir, exist_ok=True)
    
    # Define the path to the CSV file with correct naming
    csv_filename = f"{sim_name}.csv"
    csv_path = os.path.join(sim_model_dir, csv_filename)
    
    # Convert the dictionary to a DataFrame and transpose it
    # This makes parameters appear as rows instead of columns
    params_df = pd.DataFrame([setup_params]).T
    
    # Reset index to convert the parameter names to a column
    params_df.reset_index(inplace=True)
    
    # Set column names
    params_df.columns = ["Parameter", "Value"]
    
    # Check if any parameter value is excessively long
    # This is optional but helps prevent unwieldy CSV files
    for idx, row in params_df.iterrows():
        if isinstance(row["Value"], str) and len(row["Value"]) > 500:
            # Truncate extremely long values with a note
            params_df.at[idx, "Value"] = f"{row['Value'][:500]}... [truncated]"
    
    # Save to CSV with semicolon separator
    params_df.to_csv(csv_path, sep=";", index=False)
        
    return csv_path