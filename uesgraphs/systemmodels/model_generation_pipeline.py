from pathlib import Path
#import yaml
import os

import pandas as pd

from uesgraphs.uesgraph import UESGraph
from uesgraphs.systemmodels.templates import UESTemplates
from uesgraphs.utilities import set_up_file_logger, set_up_terminal_logger
from uesgraphs.systemmodels import utilities as sysmod_utils

import warnings
import logging
from datetime import datetime
import tempfile

###  MAIN FUNCTION ###

def uesgraph_to_modelica(uesgraph, simplification_level,
                         workspace,
                         sim_setup_path,
                         input_heating, input_dhw, input_cooling,
                         ground_temp_path,
                         logger=None,
                         log_level=logging.DEBUG
                         ):
    """
    Convert an Urban Energy System Graph (UESGraph) to Modelica model files.

    This function processes a UESGraph, applies simplification, adds demand data,
    and generates Modelica model files based on simulation parameters.

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
        logger = set_up_file_logger("ModelicaCodeGen", level=int(log_level))

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

    # Step 3.1: Write simulation parameters to graph (needed for connector time-series generation)
    logger.info("Writing simulation parameters to graph")
    uesgraph.graph['stop_time'] = float(sim_params['stop_time'])
    uesgraph.graph['timestep'] = sim_params.get('timestep', 900)  # Default 900s = 15min
    logger.debug(f"Set graph parameters: stop_time={uesgraph.graph['stop_time']}, timestep={uesgraph.graph['timestep']}")

    # Step 3.2: Ensure all edges have names (required for Modelica generation)
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
            assign_pipe_parameters(uesgraph, sim_setup_path, logger)
            logger.info("Pipe parameters successfully assigned")
        except Exception as e:
            logger.error(f"Failed to assign pipe parameters: {e}")
            raise

        # Step 6: Assign supply parameters from Excel
        logger.info("*** Assigning supply parameters from Excel ***")
        try:
            assign_supply_parameters(uesgraph, sim_setup_path, logger)
            logger.info("Supply parameters successfully assigned")
        except Exception as e:
            logger.error(f"Failed to assign supply parameters: {e}")
            raise

        # Step 7: Assign demand parameters from Excel
        logger.info("*** Assigning demand parameters from Excel ***")
        try:
            assign_demand_parameters(uesgraph, sim_setup_path, logger)
            logger.info("Demand parameters successfully assigned")
        except Exception as e:
            logger.error(f"Failed to assign demand parameters: {e}")
            raise

        # Step 8: Load ground temperature data for simulations
        logger.info("Loading ground temperature data")
        ground_temp_df = load_ground_temp_data(ground_temp_path)
        logger.debug(f"Ground temperature data loaded of shape: {ground_temp_df.shape}")

        # Step 9: Estimate nominal mass flow rates for pipes
        logger.info("Estimating nominal mass flow rates based on pipe diameters")
        uesgraph = sysmod_utils.estimate_m_flow_nominal_tablebased(
            graph=uesgraph,
            network_type=uesgraph.graph.get("network_type", "heating")
        )
        logger.info(f"Estimated m_flow_nominal for {uesgraph.number_of_edges()} pipe edges")

        # Step 10: Simplify the UESGraph according to the specified level
        logger.info(f"*** Start simplyfing Uesgraph with simplification level: {simplification_level} ***")
        #logger.info(f"Before simplification: {len(uesgraph.edges())} edges with total length {uesgraph.calc_network_length(network_type='heating')}")
        #uesgraph = simplify_uesgraph(uesgraph, simplification_level)
        #logger.info(f"After simplification: {len(uesgraph.edges())} edges with total length {uesgraph.calc_network_length(network_type='heating')}")

        # Step 10.1: Save the simplified UESGraph
        logger.info("Try to save uesgraph after simplification")
        try:
            uesgraph.to_json(path=str(workspace),
                        name = "transurban_seestadt_uesgraphs_simplified",
                        all_data = True,
                        prettyprint = True)
            logger.info("UESGraph after simplification saved")
        except Exception as e:
            logger.error(f"Failed to save uesgraph after simplification: {e}")

        # Step 11: Create directory structure for Modelica output files
        logger.info("Creating subfolder for modelica files")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sim_name = f"Sim{timestamp}"
        sim_model_dir = os.path.join(workspace, "models", sim_name)
        os.makedirs(sim_model_dir, exist_ok=True)
        logger.info(f"Modelica files will be saved to: {sim_model_dir}")

        # Step 12: Generate Modelica files using Excel-based simulation parameters
        logger.info("Start process of generating Modelica files using Excel parameters")
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
            generate_simulation_model(
                uesgraph=uesgraph,
                sim_name=sim_name_ix,
                sim_params=sim_params,
                ground_temp_list=ground_temp_list,
                sim_model_dir=sim_model_dir,
                sim_setup_path=sim_setup_path,
                logger=logger
            )
        except Exception as e:
            logger.error(f"Error while generating Modelica files: {e}")
            raise e

    except Exception as e:
        logger.error(f"Error while processing uesgraph: {e}")
        raise e
##############################
    
### Helper functions ###

# ============================================================================
# MAIN ASSIGNMENT FUNCTIONS
# ============================================================================
def _process_component_parameters(component_id, component_data, main_parameters, 
                                  aux_parameters, excel_params, logger):
    """
    Process MAIN and AUX parameters for a single component (node or edge).
    
    This is the core validation logic shared by all three assignment functions.
    
    Parameters
    ----------
    component_id : str or tuple
        Identifier of the component (node id or edge tuple)
    component_data : dict
        The component's data dictionary
    main_parameters : list
        List of required MAIN parameter names
    aux_parameters : list
        List of optional AUX parameter names
    excel_params : dict
        Dictionary of parameters from Excel
    logger : logging.Logger
        Logger for debug messages
        
    Returns
    -------
    missing_main : list
        List of missing MAIN parameters for this component
    missing_aux : set
        Set of missing AUX parameters for this component
    stats : dict
        Statistics dict with 'from_graph' and 'from_excel' counts
    """
    missing_main = []
    missing_aux = set()
    stats = {'from_graph': 0, 'from_excel': 0}
    
    # Process MAIN parameters
    for param in main_parameters:
        if param in component_data:
            # Parameter already in component - keep it
            stats['from_graph'] += 1
            logger.debug(f"  MAIN '{param}' found in component")
        elif param in excel_params:
            # Parameter not in component, but available in Excel - apply it
            try:
                resolved_value = resolve_parameter_value(
                    excel_params[param], component_data, param, component_id
                )
                component_data[param] = resolved_value
                stats['from_excel'] += 1
                source = f"@{excel_params[param][1:]}" if isinstance(excel_params[param], str) and excel_params[param].startswith('@') else "Excel"
                logger.debug(f"  MAIN '{param}' applied from {source}")
            except ValueError as e:
                # Reference resolution failed
                missing_main.append(param)
                logger.error(f"  MAIN '{param}': {e}")
        else:
            # Parameter missing - ERROR!
            missing_main.append(param)
            logger.error(f"  MAIN '{param}' not found")
    
    # Process AUX parameters
    for param in aux_parameters:
        if param in component_data:
            # Parameter already in component - keep it
            stats['from_graph'] += 1
            logger.debug(f"  AUX '{param}' found in component")
        elif param in excel_params:
            # Parameter not in component, but available in Excel - apply it
            try:
                resolved_value = resolve_parameter_value(
                    excel_params[param], component_data, param, component_id
                )
                component_data[param] = resolved_value
                stats['from_excel'] += 1
                source = f"@{excel_params[param][1:]}" if isinstance(excel_params[param], str) and excel_params[param].startswith('@') else "Excel"
                logger.debug(f"  AUX '{param}' applied from {source}")
            except ValueError as e:
                # Reference resolution failed - treat as missing AUX
                missing_aux.add(param)
                logger.warning(f"  AUX '{param}' reference failed: {e}")
        else:
            # Parameter missing - will use Modelica default
            missing_aux.add(param)
            logger.debug(f"  AUX '{param}' not provided - will use Modelica default")
    
    return missing_main, missing_aux, stats


def _process_component_connectors(component_id, component_data, connector_parameters,
                                   excel_params, time_array, logger):
    """
    Process connector parameters (time-series inputs) for a single component.

    Connectors are dynamic inputs to Modelica models (e.g., TIn, dpIn, Q_flow_input).
    Unlike MAIN/AUX parameters, all connectors are optional. Scalar values are
    automatically converted to constant time-series.

    Parameters
    ----------
    component_id : str or tuple
        Identifier of the component (node id or edge tuple)
    component_data : dict
        The component's data dictionary (modified in-place)
    connector_parameters : list
        List of connector names from template's get_connector_names()
    excel_params : dict
        Dictionary of parameters from Excel
    time_array : list
        Time array for converting scalars to time-series (e.g., [0, 3600, 7200, ...])
    logger : logging.Logger
        Logger for debug/warning messages

    Returns
    -------
    missing_connectors : list
        List of connectors that were not provided
    stats : dict
        Statistics dict with 'from_graph', 'from_excel', 'converted' counts

    Notes
    -----
    Processing logic:
    1. If connector already in component_data:
       - Keep existing value (don't overwrite)
       - Convert scalar to time-series if needed
    2. If connector in Excel:
       - Resolve value (@ references, direct values)
       - Convert scalar to time-series
    3. If connector missing:
       - Add to missing_connectors (WARNING, not ERROR)
    """
    missing_connectors = []
    stats = {'from_graph': 0, 'from_excel': 0, 'converted': 0}

    for connector in connector_parameters:
        if connector in component_data:
            # Connector already in component - keep it, but check if conversion needed
            value = component_data[connector]

            # Convert scalar to time-series if needed
            if isinstance(value, (int, float)):
                component_data[connector] = [value] * len(time_array)
                stats['from_graph'] += 1
                stats['converted'] += 1
                logger.debug(f"  Connector '{connector}' from component (scalar to time-series)")
            elif isinstance(value, list):
                stats['from_graph'] += 1
                logger.debug(f"  Connector '{connector}' from component (time-series)")
            else:
                # Unexpected type - keep as is but warn
                stats['from_graph'] += 1
                logger.warning(f"  Connector '{connector}' has unexpected type: {type(value)}")

        elif connector in excel_params:
            # Connector not in component, but available in Excel - apply it
            try:
                resolved_value = resolve_parameter_value(
                    value=excel_params[connector],
                    component_data=component_data,
                    param_name=connector,
                    component_id=component_id,
                    time_array=time_array,
                    as_timeseries=True  # Connectors are always converted to time-series
                )
                component_data[connector] = resolved_value
                stats['from_excel'] += 1
                if isinstance(excel_params[connector], (int, float)):
                    stats['converted'] += 1
                source = f"@{excel_params[connector][1:]}" if isinstance(excel_params[connector], str) and excel_params[connector].startswith('@') else "Excel"
                logger.debug(f"  Connector '{connector}' applied from {source}")
            except ValueError as e:
                # Reference resolution failed - treat as missing
                missing_connectors.append(connector)
                logger.warning(f"  Connector '{connector}': {e}")
        else:
            # Connector missing - this is OK (connectors are optional)
            missing_connectors.append(connector)
            logger.debug(f"  Connector '{connector}' not provided")

    return missing_connectors, stats


def assign_pipe_parameters(uesgraph, excel_path, logger=None):
    """
    Assign parameters to pipe edges in the uesgraph according to the flow chart logic.

    This function follows the validation flow:
    1. Load Excel parameters and extract template configuration
    2. Load and parse the template file (standard or custom based on Excel)
    3. Extract MAIN (required) and AUX (optional) parameters
    4. For each edge individually:
       - Check MAIN parameters: in edge: keep, not in edge: try Excel, missing: ERROR
       - Check AUX parameters: in edge: keep, not in edge: try Excel, missing: WARNING
    5. Apply parameters from Excel where needed (never overwrite existing edge attributes)
    6. Support @ references: Excel values starting with @ are resolved to edge attributes

    Parameters
    ----------
    uesgraph : UESGraph
        The urban energy system graph object (modified in-place)
    excel_path : str or Path
        Path to Excel file containing component parameters and template configuration
        Excel should have either 'template' (for standard) or 'template_path' (for custom)
    logger : logging.Logger, optional
        Logger for status messages and warnings
        If None, creates a default logger

    Returns
    -------
    uesgraph : UESGraph
        The updated graph object (same as input, modified in-place)

    Raises
    ------
    ValueError
        If neither 'template' nor 'template_path' found in Excel
        If required MAIN parameters are missing for any edge

    Warns
    -----
    UserWarning
        If optional AUX parameters are missing (will use Modelica defaults)
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.assign_pipe_parameters")

    # Step 1: Load Excel parameters (mandatory)
    excel_params = _load_excel(excel_path, 'Pipes', logger)

    # Step 2: Load template file (from Excel config)
    model_name = excel_params.get('template')
    template_path = excel_params.get('template_path')
    main_parameters, aux_parameters, connector_parameters = parse_template_parameters(
        'Pipe', model_name, template_path, logger
    )

    # Step 3: Get time array for connector conversion
    stop_time = uesgraph.graph.get('stop_time')
    timestep = uesgraph.graph.get('timestep')
    if stop_time and timestep:
        time_array = [x * timestep for x in range(int((stop_time / timestep) + 1))]
    else:
        time_array = []
        if connector_parameters:
            logger.warning("Connectors found but no time_array available (stop_time/timestep not set)")

    # Step 4: Process each edge individually
    total_edges = len(list(uesgraph.edges()))
    logger.info(f"Processing {total_edges} edge(s)...")

    all_missing_main = []
    all_missing_aux = set()
    all_missing_connectors = set()
    all_stats = []
    all_connector_stats = []

    for edge_idx, edge in enumerate(uesgraph.edges(), 1):
        edge_data = uesgraph.edges[edge]
        logger.debug(f"Processing edge {edge_idx}/{total_edges}: {edge}")

        if template_path is not None:
            uesgraph.edges[edge]['template_path'] = str(template_path)
        # Process parameters
        missing_main, missing_aux, stats = _process_component_parameters(
            edge, edge_data, main_parameters, aux_parameters,
            excel_params, logger
        )

        # Process connectors
        missing_connectors, connector_stats = _process_component_connectors(
            edge, edge_data, connector_parameters, excel_params,
            time_array, logger
        )

        # Collect results
        all_missing_main.extend([(edge, param) for param in missing_main])
        all_missing_aux.update(missing_aux)
        all_missing_connectors.update(missing_connectors)
        all_stats.append(stats)
        all_connector_stats.append(connector_stats)

    # Step 5: Aggregate and report results
    total_stats = _aggregate_statistics(all_stats)
    total_connector_stats = _aggregate_statistics(all_connector_stats)
    _check_and_report_results(
        'edge', total_edges, all_missing_main, all_missing_aux,
        all_missing_connectors, total_stats, total_connector_stats, logger
    )

    return uesgraph


def assign_supply_parameters(uesgraph, excel_path, logger=None):
    """
    Assign parameters to supply nodes in the uesgraph according to the flow chart logic.
    
    This function follows the validation flow:
    1. Load and parse the template file
    2. Extract MAIN (required) and AUX (optional) parameters
    3. Load Excel parameters if provided
    4. For each supply node individually:
       - Check MAIN parameters: in node: keep, not in node: try Excel, missing: ERROR
       - Check AUX parameters: in node: keep, not in node: try Excel, missing: WARNING
    5. Apply parameters from Excel where needed (never overwrite existing node attributes)
    6. Support @ references: Excel values starting with @ are resolved to node attributes
    
    Parameters
    ----------
    uesgraph : UESGraph
        The urban energy system graph object (modified in-place)
    template_path : str or Path
        Path to the supply template file (.mako)
    excel_path : str or Path, optional
        Path to Excel file containing component parameters
        If None, only graph attributes are used
    logger : logging.Logger, optional
        Logger for status messages and warnings
        If None, creates a default logger
        
    Returns
    -------
    uesgraph : UESGraph
        The updated graph object (same as input, modified in-place)
        
    Raises
    ------
    FileNotFoundError
        If template file not found
    ValueError
        If required MAIN parameters are missing for any supply node
        
    Warns
    -----
    UserWarning
        If optional AUX parameters are missing (will use Modelica defaults)
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.assign_supply_parameters")

    # Step 1: Load Excel parameters (mandatory)
    excel_params = _load_excel(excel_path, 'Supply', logger)

    # Step 2: Load template file (from Excel config)
    model_name = excel_params.get('template')
    template_path = excel_params.get('template_path')
    main_parameters, aux_parameters, connector_parameters = parse_template_parameters(
        'Supply', model_name, template_path, logger
    )

    # Step 3: Get time array for connector conversion
    stop_time = uesgraph.graph.get('stop_time')
    timestep = uesgraph.graph.get('timestep')
    if stop_time and timestep:
        time_array = [x * timestep for x in range(int((stop_time / timestep) + 1))]
    else:
        time_array = []
        if connector_parameters:
            logger.warning("Connectors found but no time_array available (stop_time/timestep not set)")

    # Step 4: Find supply nodes
    network_type = uesgraph.graph.get("network_type", "heating")
    is_supply_key = f"is_supply_{network_type}"

    supply_nodes = [
        node for node in uesgraph.nodelist_building
        if uesgraph.nodes[node].get(is_supply_key, False)
    ]

    if not supply_nodes:
        warning_msg = f"No supply nodes found (looking for '{is_supply_key}' = True)"
        logger.warning(warning_msg)
        warnings.warn(warning_msg, UserWarning)
        return uesgraph

    # Step 5: Process each supply node individually
    total_nodes = len(supply_nodes)
    logger.info(f"Processing {total_nodes} supply node(s)...")

    all_missing_main = []
    all_missing_aux = set()
    all_missing_connectors = set()
    all_stats = []
    all_connector_stats = []

    for node_idx, node in enumerate(supply_nodes, 1):
        node_data = uesgraph.nodes[node]
        logger.debug(f"Processing supply node {node_idx}/{total_nodes}: {node}")

        if template_path is not None:
            uesgraph.nodes[node]['template_path'] = str(template_path)
        
        # Process parameters
        missing_main, missing_aux, stats = _process_component_parameters(
            node, node_data, main_parameters, aux_parameters,
            excel_params, logger
        )

        # Process connectors
        missing_connectors, connector_stats = _process_component_connectors(
            node, node_data, connector_parameters, excel_params,
            time_array, logger
        )

        # Collect results
        all_missing_main.extend([(node, param) for param in missing_main])
        all_missing_aux.update(missing_aux)
        all_missing_connectors.update(missing_connectors)
        all_stats.append(stats)
        all_connector_stats.append(connector_stats)

    # Step 6: Aggregate and report results
    total_stats = _aggregate_statistics(all_stats)
    total_connector_stats = _aggregate_statistics(all_connector_stats)
    _check_and_report_results(
        'supply node', total_nodes, all_missing_main, all_missing_aux,
        all_missing_connectors, total_stats, total_connector_stats, logger
    )

    return uesgraph


def assign_demand_parameters(uesgraph, excel_path, logger=None):
    """
    Assign parameters to demand nodes in the uesgraph according to the flow chart logic.
    
    This function follows the validation flow:
    1. Load and parse the template file
    2. Extract MAIN (required) and AUX (optional) parameters
    3. Load Excel parameters if provided
    4. For each demand node individually:
       - Check MAIN parameters: in node: keep, not in node: try Excel, missing: ERROR
       - Check AUX parameters: in node: keep, not in node: try Excel, missing: WARNING
    5. Apply parameters from Excel where needed (never overwrite existing node attributes)
    6. Support @ references: Excel values starting with @ are resolved to node attributes
    
    Parameters
    ----------
    uesgraph : UESGraph
        The urban energy system graph object (modified in-place)
    template_path : str or Path
        Path to the demand template file (.mako)
    excel_path : str or Path, optional
        Path to Excel file containing component parameters
        If None, only graph attributes are used
    logger : logging.Logger, optional
        Logger for status messages and warnings
        If None, creates a default logger
        
    Returns
    -------
    uesgraph : UESGraph
        The updated graph object (same as input, modified in-place)
        
    Raises
    ------
    FileNotFoundError
        If template file not found
    ValueError
        If required MAIN parameters are missing for any demand node
        
    Warns
    -----
    UserWarning
        If optional AUX parameters are missing (will use Modelica defaults)
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.assign_demand_parameters")

    # Step 1: Load Excel parameters (mandatory)
    excel_params = _load_excel(excel_path, 'Demands', logger)

    # Step 2: Load template file (from Excel config)
    model_name = excel_params.get('template')
    template_path = excel_params.get('template_path')
    main_parameters, aux_parameters, connector_parameters = parse_template_parameters(
        'Demand', model_name, template_path, logger
    )

    # Step 3: Get time array for connector conversion
    stop_time = uesgraph.graph.get('stop_time')
    timestep = uesgraph.graph.get('timestep')
    if stop_time and timestep:
        time_array = [x * timestep for x in range(int((stop_time / timestep) + 1))]
    else:
        time_array = []
        if connector_parameters:
            logger.warning("Connectors found but no time_array available (stop_time/timestep not set)")

    # Step 4: Find demand nodes (buildings that are NOT supply)
    network_type = uesgraph.graph.get("network_type", "heating")
    is_supply_key = f"is_supply_{network_type}"

    demand_nodes = [
        node for node in uesgraph.nodelist_building
        if not uesgraph.nodes[node].get(is_supply_key, False)
    ]

    if not demand_nodes:
        warning_msg = f"No demand nodes found (looking for buildings with '{is_supply_key}' = False)"
        logger.warning(warning_msg)
        warnings.warn(warning_msg, UserWarning)
        return uesgraph

    # Step 5: Process each demand node individually
    total_nodes = len(demand_nodes)
    logger.info(f"Processing {total_nodes} demand node(s)...")

    all_missing_main = []
    all_missing_aux = set()
    all_missing_connectors = set()
    all_stats = []
    all_connector_stats = []

    for node_idx, node in enumerate(demand_nodes, 1):
        node_data = uesgraph.nodes[node]
        logger.debug(f"Processing demand node {node_idx}/{total_nodes}: {node}")

        # Process parameters
        missing_main, missing_aux, stats = _process_component_parameters(
            node, node_data, main_parameters, aux_parameters,
            excel_params, logger
        )

        if template_path is not None:
            uesgraph.nodes[node]['template_path'] = str(template_path)

        # Process connectors
        missing_connectors, connector_stats = _process_component_connectors(
            node, node_data, connector_parameters, excel_params,
            time_array, logger
        )

        # Collect results
        all_missing_main.extend([(node, param) for param in missing_main])
        all_missing_aux.update(missing_aux)
        all_missing_connectors.update(missing_connectors)
        all_stats.append(stats)
        all_connector_stats.append(connector_stats)

    # Step 6: Aggregate and report results
    total_stats = _aggregate_statistics(all_stats)
    total_connector_stats = _aggregate_statistics(all_connector_stats)
    _check_and_report_results(
        'demand node', total_nodes, all_missing_main, all_missing_aux,
        all_missing_connectors, total_stats, total_connector_stats, logger
    )

    return uesgraph


def resolve_parameter_value(value, component_data, param_name, component_id,
                           time_array=None, as_timeseries=False):
    """
    Resolve parameter value - handles direct values, @references, and optional time-series conversion.

    This function is used by both parameter and connector processing to resolve values from Excel.
    It supports:
    - Direct values (int, float, bool, str, list)
    - @ References to component attributes
    - Scalar to time-series conversion for connectors

    Parameters
    ----------
    value : any
        The parameter value from Excel (can be direct value or @reference)
    component_data : dict
        The component's data dictionary (node or edge attributes)
    param_name : str
        Name of the parameter being resolved
    component_id : str or tuple
        Identifier of the component (node id or edge tuple)
    time_array : list, optional
        Time array for converting scalars to time-series. Required if as_timeseries=True.
    as_timeseries : bool, optional
        If True, convert scalar values to constant time-series. Default is False.

    Returns
    -------
    resolved_value : any
        The resolved parameter value

    Raises
    ------
    ValueError
        If @reference not found or time_array missing when as_timeseries=True

    Notes
    -----
    Future extensions could include:
    - CSV file path loading (e.g., value="path/to/timeseries.csv")
    - Multiple column selection from CSVs
    - Interpolation for time-series with different timesteps

    Examples
    --------
    >>> # Direct scalar value
    >>> resolve_parameter_value(353.15, {}, 'TReturn', 'node1')
    353.15

    >>> # @ Reference
    >>> node_data = {'heatDemand_max': 800000}
    >>> resolve_parameter_value('@heatDemand_max', node_data, 'Q_nominal', 'node1')
    800000

    >>> # Scalar to time-series conversion
    >>> time = [0, 3600, 7200]
    >>> resolve_parameter_value(353.15, {}, 'TIn', 'node1', time, as_timeseries=True)
    [353.15, 353.15, 353.15]
    """
    resolved = value

    # Handle @ references
    if isinstance(value, str) and value.startswith('@'):
        attr_name = value[1:]  # Remove '@' prefix
        if attr_name not in component_data:
            raise ValueError(
                f"Component {component_id}: Parameter '{param_name}' references "
                f"non-existent attribute '@{attr_name}'"
            )
        resolved = component_data[attr_name]
    else:
        # Direct value
        resolved = value

    # Convert scalar to time-series if requested
    if as_timeseries and isinstance(resolved, (int, float)):
        if time_array is None:
            raise ValueError(
                f"Component {component_id}: Cannot convert '{param_name}' to time-series "
                f"without time_array"
            )
        resolved = [resolved] * len(time_array)

    return resolved


def parse_template_parameters(model_type, model_name=None, template_path=None, logger=None):
    """
    Parse template to extract required, optional, and connector parameters using UESTemplates.

    Parameters
    ----------
    model_type : str
        Component type: "Supply", "Demand", or "Pipe"
    model_name : str, optional
        Modelica class name for standard templates (e.g., "OpenLoop.SourceIdeal")
    template_path : str or Path, optional
        Path to custom template file
    logger : logging.Logger, optional
        Logger for status messages

    Returns
    -------
    tuple (list, list, list)
        (main_parameters, aux_parameters, connector_parameters)

    Raises
    ------
    ValueError
        If neither model_name nor template_path is provided, or both are None
    Exception
        If template parsing fails

    Examples
    --------
    # Standard template:
    >>> main, aux, conn = parse_template_parameters('Supply', model_name='OpenLoop.SourceIdeal')
    >>> main
    ['pReturn', 'TReturn']
    >>> conn
    ['TIn', 'dpIn']

    # Custom template:
    >>> main, aux, conn = parse_template_parameters('Supply', template_path='/path/custom.mako')
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.parse_template_parameters")

    # Validation - treat None as not provided
    if (not model_name or model_name is None) and (not template_path or template_path is None):
        raise ValueError("Either model_name or template_path must be provided")

    # Warning if both are provided
    if model_name and template_path and template_path is not None:
        logger.warning(f"Both model_name ('{model_name}') and template_path ('{template_path}') provided. "
                      f"Using custom template at template_path, ignoring model_name.")

    try:
        if template_path and template_path is not None:
            logger.debug(f"Loading custom template: {template_path}")
            effective_model_name = "CustomTemplate"  # Dummy name
            effective_template_path = template_path
        else:
            logger.debug(f"Loading standard template for {model_type}: {model_name}")
            effective_model_name = model_name
            effective_template_path = None

        template = UESTemplates(
            model_name=effective_model_name,
            model_type=model_type,
            template_path=effective_template_path
        )

        # Extract parameters
        main_params = template.call_function("get_main_parameters")
        aux_params = template.call_function("get_aux_parameters")
        connector_params = template.call_function("get_connector_names")

        logger.info(f"Template parsed: {len(main_params)} main, {len(aux_params)} aux, "
                   f"{len(connector_params)} connector parameters")

        return main_params, aux_params, connector_params

    except Exception as e:
        error_msg = f"Failed to parse template: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)


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
    required = ['simulation_name', 'solver', 'start_time', 'stop_time', 'tolerance', 'medium']
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


def _aggregate_statistics(all_stats_list):
    """Aggregate statistics from multiple components."""
    total_stats = {'from_graph': 0, 'from_excel': 0}
    for stats in all_stats_list:
        total_stats['from_graph'] += stats['from_graph']
        total_stats['from_excel'] += stats['from_excel']
    return total_stats


def _check_and_report_results(component_type, component_count, all_missing_main,
                              all_missing_aux, all_missing_connectors,
                              total_stats, total_connector_stats, logger):
    """
    Check if validation was successful and report results.

    Parameters
    ----------
    component_type : str
        Type of component ('edge', 'supply node', 'demand node')
    component_count : int
        Number of components processed
    all_missing_main : list of tuples
        List of (component_id, param) tuples for missing MAIN parameters
    all_missing_aux : set
        Set of AUX parameter names missing across all components
    all_missing_connectors : set
        Set of connector names missing across all components
    total_stats : dict
        Aggregated statistics for parameters
    total_connector_stats : dict
        Aggregated statistics for connectors
    logger : logging.Logger
        Logger instance

    Raises
    ------
    ValueError
        If any MAIN parameters are missing
    """
    # Report parameter summary
    logger.info(f"Processed {component_count} {component_type}(s)")
    logger.info(f"  - Parameters from graph: {total_stats['from_graph']}")
    logger.info(f"  - Parameters from Excel: {total_stats['from_excel']}")

    # Report connector summary (if any connectors were found)
    if total_connector_stats['from_graph'] > 0 or total_connector_stats['from_excel'] > 0:
        logger.info(f"  - Connectors from graph: {total_connector_stats['from_graph']}")
        logger.info(f"  - Connectors from Excel: {total_connector_stats['from_excel']}")
        if total_connector_stats.get('converted', 0) > 0:
            logger.info(f"  - Scalars converted to time-series: {total_connector_stats['converted']}")

    # Summary of missing AUX parameters
    if all_missing_aux:
        missing_count = len(all_missing_aux)
        warning_msg = (
            f"{missing_count} AUX parameter(s) not provided for {component_type}s, "
            f"will use Modelica defaults: {', '.join(sorted(all_missing_aux))}"
        )
        logger.warning(warning_msg)
        warnings.warn(warning_msg, UserWarning)

    # Summary of missing connectors (ERROR - connectors are required!)
    if all_missing_connectors:
        missing_count = len(all_missing_connectors)
        connector_list = ', '.join(sorted(all_missing_connectors))
        first_connector = list(all_missing_connectors)[0]
        error_msg = (
            f"Validation FAILED: {missing_count} required connector(s) missing for {component_type}s\n"
            f"Missing connectors: {connector_list}\n\n"
            f"Connectors are time-series inputs required by Modelica templates.\n\n"
            f"HOW TO FIX:\n"
            f"Option 1 - Define in Excel sheet:\n"
            f"  - Open the Excel configuration file\n"
            f"  - Go to the '{component_type.capitalize()}' sheet\n"
            f"  - Add rows: Parameter='{first_connector}', Value=<number or @reference>\n"
            f"  - Example: Parameter='TIn', Value=353.15 (will be converted to constant time-series)\n\n"
            f"Option 2 - Define on UESGraph before calling pipeline:\n"
            f"  - For {component_type}s: uesgraph.{component_type}[component_id]['{first_connector}'] = value\n"
            f"  - Example: uesgraph.nodes['supply1']['TIn'] = 353.15\n\n"
            f"Note: Scalar values are automatically converted to constant time-series.\n"
            f"      Use @references to point to existing attributes (e.g., Value='@supply_temp')"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Check if validation was successful
    if all_missing_main:
        error_count = len(all_missing_main)
        error_msg = (
            f"Validation FAILED: {error_count} missing MAIN parameter(s)\n"
            f"Missing parameters per {component_type}:\n"
        )
        for component_id, param in all_missing_main:
            error_msg += f"  - {component_type.capitalize()} {component_id}: '{param}'\n"
        error_msg += (
            f"\nFix suggestions:\n"
            f"  - If parameter varies per {component_type}: add to uesgraph attributes\n"
            f"  - If parameter is same for all {component_type}s: add to Excel sheet"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    else:
        logger.info("All MAIN parameters successfully validated and applied")


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
#### Modelica code generation

def generate_simulation_model(uesgraph, sim_name, sim_params, ground_temp_list, sim_model_dir, sim_setup_path, logger=None):
    """
    Generate Modelica simulation model using Excel-based parameter system.

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
        Directory to save Modelica files
    sim_setup_path : str
        Path to Excel configuration file (needed to load template names)
    logger : logging.Logger, optional
        Logger instance
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.generate_simulation_model")

    logger.info("Setting up UESGraph for Modelica generation")

    # Ensure node names are strings
    for node in list(uesgraph.nodes()):
        uesgraph.nodes[node]["name"] = str(uesgraph.nodes[node]["name"])

    # Set network type
    uesgraph.graph["network_type"] = "heating"

    # Create metadata
    meta_data = create_meta_data(sim_name, sim_params)

  
    # Load template names from Excel sheets (needed for create_model)
    logger.info("Loading template names from Excel configuration")
    pipe_params = load_component_parameters(excel_path=sim_setup_path, component_type='Pipes')
    supply_params = load_component_parameters(excel_path=sim_setup_path, component_type='Supply')
    demand_params = load_component_parameters(excel_path=sim_setup_path, component_type='Demands')

    # Get template names (prefer template_path if provided, otherwise use template name)
    model_pipe = pipe_params.get('template_path') or pipe_params.get('template')
    model_supply = supply_params.get('template_path') or supply_params.get('template')
    model_demand = demand_params.get('template_path') or demand_params.get('template')

    logger.info(f"Using templates: pipe={model_pipe}, supply={model_supply}, demand={model_demand}")

    # Create system model
    logger.info("Creating system model with pre-assigned parameters")
    from uesgraphs.systemmodels import utilities as sysmod_utils

    sysmod_utils.create_model(
        name=sim_name,
        save_at=sim_model_dir,
        graph=uesgraph,
        stop_time=float(sim_params["stop_time"]),
        timestep=sim_params.get("timestep",900),  # Could be made configurable
        model_supply=model_supply,
        model_demand=model_demand,
        model_pipe=model_pipe,
        model_medium=sim_params["medium"],
        model_ground="t_ground_table",
        T_nominal=sim_params.get("T_nominal", 273.15 + 20),
        p_nominal=sim_params.get("p_nominal",4e5),
        fraction_glycol=sim_params.get("fraction_glycol",0.3),
        solver=sim_params["solver"],
        t_ground_prescribed=ground_temp_list,
        short_pipes_static=None,  # Could be made configurable
        meta_data=meta_data,
    )

    logger.info(f"Modelica model generated successfully: {sim_name}")

def create_meta_data(sim_name, sim_params):
    """Create metadata dictionary from Excel simulation parameters."""
    return {
        "simulation_name": sim_name,
        "solver": sim_params["solver"],
        "start_time": float(sim_params["start_time"]),
        "stop_time": float(sim_params["stop_time"]),
        "tolerance": float(sim_params["tolerance"]),
        "medium": sim_params["medium"],
        "created_at": datetime.now().isoformat()
    }


#### Process demand data and assign to uesgraph

def combine_heating_dhw(heat_demand, dhw_demand):
    """
    Combines heating and DHW demands where both are non-zero for peak load calc.
    """
    heating_combined = []
    dhw_adjusted = []
    
    for heat_val, dhw_val in zip(heat_demand, dhw_demand):
        if heat_val != 0.0 and dhw_val != 0.0:
            heating_combined.append(heat_val + dhw_val)
            dhw_adjusted.append(0.0)
        else:
            heating_combined.append(heat_val)
            dhw_adjusted.append(dhw_val)
            
    return heating_combined, dhw_adjusted

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
        
        #Combine heating and DHW demands where both are non_zero
                #Only used for max demand calculation
        if demand_mode ==0:
            heating_combined, dhw_adjusted = combine_heating_dhw(demands["heating"], demands["dhw"])

        #Save demands to node
        node = uesgraph.nodes[bldg_node]
        node.update({
            "input_dhw": demands["dhw"],
            "input_heat": demands["heating"],
            "input_cool": demands["cooling"],
            "heatDemand_max": max(max(heating_combined), max(dhw_adjusted)),
            "coldDemand_max": max(demands["cooling"])
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
