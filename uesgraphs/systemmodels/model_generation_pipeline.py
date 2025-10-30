from pathlib import Path
import yaml
import os

import pandas as pd

from uesgraphs.uesgraph import UESGraph



import logging
from datetime import datetime
import tempfile


### Logging function

def set_up_logger(name,log_dir = None,level=int(logging.ERROR)):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if log_dir == None:
            log_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
        print(f"Logfile findable here: {log_file}")
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

##############################

###  MAIN FUNCTION ###

def uesgraph_to_modelica(uesgraph, simplification_level,
                         workspace,
                         sim_setup_path,
                         input_heating, input_dhw, input_cooling,
                         ground_temp_path,
                         log_dir=None,
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
    log_dir : str or Path, optional
        Directory to save log files (default is None, logs to tmp directory)
    log_level : int, optional
        Logging level (default is logging.DEBUG)
        
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
    logger = set_up_logger("ModelicaCodeGen",level=int(log_level), log_dir=log_dir)
    
    # Step 1: Validate input files and folders    logger.info("Validating files")
    paths_to_check = [sim_setup_path, input_heating, input_dhw, input_cooling, ground_temp_path]
    existing_files, missing_files = validate_paths(paths_to_check)
    if missing_files:
        logger.error(f"Missing files: {missing_files}")
        raise FileNotFoundError("Some files are missing. Please check the logs for details.")
    logger.debug(f"Existing files: {existing_files}")

    # Step 2: Load simulation configuration
    logger.info("Loading simulation settings")
    sim_setup_dict = load_simulation_settings(sim_setup_path)
    logger.debug(f"Simulation settings loaded: {sim_setup_dict}")

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
    
    
    try:
        #Step 4: Assign demand data to the graph nodes
        logger.info("Assigning demand data")
        input_paths_dict = {
            "heating": input_heating,
            "cooling": input_cooling,
            "dhw": input_dhw
        }
        uesgraph, msg = assign_demand_data(uesgraph, input_paths_dict)
        logger.debug(msg)

        # Step 5: Save the UESGraph with added demand data
        logger.info("Try to save uesgraph with demand data")
        try:
            uesgraph.to_json(path=str(workspace),
                        name = "transurban_seestadt_uesgraphs_with_demand",
                        all_data = True,
                        prettyprint = True)
            logger.info("UESGraph with demand data saved")
        except Exception as e:
            logger.error(f"Failed to save uesgraph with demand data: {e}")

        # Step 6: Load ground temperature data for simulations
        logger.info("Loading ground temperature data")
        ground_temp_df = load_ground_temp_data(ground_temp_path)
        logger.debug(f"Ground temperature data loaded of shape: {ground_temp_df.shape}")

        # Step 7: Simplify the UESGraph according to the specified level
        logger.info(f"*** Start simplyfing Uesgraph with simplification level: {simplification_level} ***")
        logger.info(f"Before simplification: {len(uesgraph.edges())} edges with total length {uesgraph.calc_network_length(network_type='heating')}")
        uesgraph = simplify_uesgraph(uesgraph, simplification_level)
        logger.info(f"After simplification: {len(uesgraph.edges())} edges with total length {uesgraph.calc_network_length(network_type='heating')}")
    
        # Step 8: Save the simplified UESGraph
        logger.info("Try to save uesgraph after simplification")
        try:
            uesgraph.to_json(path=str(workspace),
                        name = "transurban_seestadt_uesgraphs_simplified",
                        all_data = True,
                        prettyprint = True)
            logger.info("UESGraph after simplification saved")
        except Exception as e:
            logger.error(f"Failed to save uesgraph after simplification: {e}")
        
        # Step 9: Create directory structure for Modelica output files
        logger.info("Creating subfolder for modelica files")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sim_name = f"Sim{timestamp}"
        sim_model_dir = os.path.join(workspace, "models", sim_name)
        os.makedirs(sim_model_dir, exist_ok=True)
        logger.info(f"Modelica files will be saved to: {sim_model_dir}")

        # Step 10: Generate Modelica files for each simulation configuration
        logger.info(f"Start process of generating Modelica files for: {len(sim_setup_dict)} simulations")
        for setup_params in sim_setup_dict:
            sim_name_ix = f"{sim_name}_{str(setup_params["Simulation Name"])}"
            logger.info(f"Processing simulation parameters: {setup_params}")
            ground_temp_list = ground_temp_df[setup_params["ground_depth"]].tolist()
            logger.info(f"Using ground temperature data for depth {setup_params['ground_depth']}")
            #uesgraph_copy = uesgraph.copy()
            uesgraph = map_setup_to_uesgraph(uesgraph=uesgraph, setup_params=setup_params)
            
            if setup_params["save_params_to_csv"]: 
                logger.info("Saving setup parameters to CSV")
                save_setup_params_to_csv(setup_params, sim_name_ix, sim_model_dir)
            
            try:
                logger.info(f"Start creating model for simulation: {sim_name_ix}")
                generate_simulation_model(uesgraph=uesgraph,
                                sim_name=sim_name_ix,
                                setup_params=setup_params,
                                ground_temp_list=ground_temp_list,
                                sim_model_dir = sim_model_dir,
                )
            except Exception as e:
                logger.error(f"Error while generating Modelica files: {e}")
                raise e

    except Exception as e:
        logger.error(f"Error while processing uesgraph: {e}")
        raise e
##############################
    
### Helper functions ###
    
#### Modelica code generation
def generate_simulation_model(uesgraph,setup_params,sim_name,
                     sim_model_dir, ground_temp_list):
    for node in list(uesgraph.nodes()):
        uesgraph.nodes[node]["name"] = str(uesgraph.nodes[node]["name"])

    #replace diameter ??

    uesgraph.graph["network_type"] ="heating"

    uesgraph = setup_building_parameters(uesgraph, setup_params)

    uesgraph = setup_pipe_parameters(uesgraph, setup_params)

    meta_data = create_meta_data(sim_name, setup_params)

    from uesgraphs.systemmodels import utilities as sysmod_utils

    uesgraph = sysmod_utils.estimate_m_flow_nominal_tablebased(
        graph = uesgraph,
        network_type = "heating"
    )
  

    sysmod_utils.create_model(
            name=sim_name,
            save_at=sim_model_dir,
            graph=uesgraph,
            stop_time=365 * 24 * 3600,
            timestep=900,
            model_supply=str(setup_params["template_path_supply"]),
            model_demand=str(setup_params["template_path_demand"]),
            model_pipe=setup_params["comp_model_pipe"],#Kind of senseless since used template is determined by template_path or comp_model as attribute of the edge
            model_medium=setup_params["Medium"],
            model_ground="t_ground_table",
            T_nominal=273.15 + 0,
            p_nominal=4e5,
            fraction_glycol=0.3,
            solver=setup_params["solver"],
            t_ground_prescribed=ground_temp_list,
            short_pipes_static=setup_params["static_pipe_length"],
            # short_pipes_static=2,
            meta_data=meta_data,
        )

def setup_building_parameters(uesgraph, params_dict):
    """Configure building parameters based on type (supply or demand)."""
    
    # Common parameters for all buildings
    common_params = {
        'allowFlowReversal': params_dict['allowFlowReversal']
    }
    
    # Specific parameters for demand buildings
    demand_params = {
        'template_path': str(params_dict['template_path_demand']),
        'dp_nominal': params_dict['dp_nominal'],
        'dT_Network': params_dict['dT_Network'],
        'T_dhw_supply': params_dict['T_dhw_supply'],
        'T_heat_supply': params_dict['T_heat_supply'],
        'T_cold_supply': params_dict['T_cold_supply'],
    }
    
    # Specific parameters for supply buildings
    supply_params = {
        'template_path': str(params_dict['template_path_supply']),
        'heatDemand_max_supply': params_dict['heatDemand_max_supply'], 
        'dT_Network': params_dict['dT_Network'],
        'T_dhw_supply': params_dict['T_dhw_supply'],
        'T_heat_supply': params_dict['T_heat_supply'],
        'T_cold_supply': params_dict['T_cold_supply'],
    }
    
    # Update all nodes
    for node in uesgraph.nodelist_building:
        node_data = uesgraph.nodes[node]
        
        # Update common parameters first
        node_data.update(common_params)
        
        if not node_data['is_supply_heating']:
            # Demand building
            node_data.update(demand_params)
        else:
            # Supply building
            node_data.update(supply_params)
    return uesgraph

def setup_pipe_parameters(uesgraph, params_dict):
    """
    Configure pipe parameters for all edges in the network graph.
    
    Args:
        graph: uesgraphs graph containing the network structure
        params_dict: dictionary containing configuration parameters
    """
    pipe_params = {
        'template_path': params_dict['template_path_pipe'], #Has to be None to use the Aixlib default template in uesgraphs, otherwise
#        "comp_model": params_dict['comp_model_pipe'],
        'dIns': params_dict['dIns'],                    # Insulation diameter
        'kIns': params_dict['kIns'],                    # Insulation thermal conductivity
        'fac': params_dict['fac'],                      # Scaling factor
        'roughness': params_dict['roughness'],          # Pipe roughness
        'allowFlowReversal': params_dict['allowFlowReversal'],
    }
    
    # Update pipe parameters for each edge
    for edge in uesgraph.edges():
        # Copy base parameters
        uesgraph.edges[edge].update(pipe_params)
        # Set hydraulic diameter based on edge-specific inner diameter
        uesgraph.edges[edge]['dh'] = uesgraph.edges[edge]['diameter']

    return uesgraph

def create_meta_data(sim_name, setup_params):
    meta_data = {
        "General": "Nothing",
        "Modelname": sim_name,
        "template_demand": setup_params["template_path_demand"],
        "template_supply": setup_params["template_path_supply"],
        "Parameters_dict": setup_params.copy(),
    }
    return meta_data
#### Process sim_setup modifications

def map_setup_to_uesgraph(uesgraph, setup_params):
    """
    Maps simulation setup parameters to a UESGraph object, specifically handling
    the linking of demands to resources.
    
    This function checks if demands should be linked to resources based on the
    'link_demands_to_ressources' parameter. If linking is required, it verifies
    that the template supports this functionality and updates node attributes
    for non-supply heating nodes.
    
    Parameters:
    -----------
    uesgraph : UESGraph
        The urban energy system graph to be modified
    setup_params : dict
        Dictionary containing simulation setup parameters, must include 
        'link_demands_to_ressources' key
    template_demand : str
        Path to the demand template file
        
    Returns:
    --------
    UESGraph
        The modified urban energy system graph with updated node attributes
        
    Raises:
    -------
    KeyError: If 'link_demands_to_ressources' is not found in setup parameters
    ValueError: If demand template doesn't support resource linking when required
    Exception: For other processing errors
    """
    try:
        link_value = setup_params["link_demands_to_ressources"]
        
        # Handle different data types for the link_value parameter
        if isinstance(link_value, bool):
            is_linked = link_value
        elif isinstance(link_value, (int, float)):
            is_linked = link_value != 0
        elif isinstance(link_value, str):
            is_linked = link_value.lower() in ('true', 'yes', 'y', '1')
        else:
            # Fallback for other data types
            is_linked = bool(link_value)
        
        # If linking is required, process the demand template and update nodes
        if is_linked:
            # Read the demand template file and check for the loadResource function
            with open(setup_params["template_path_demand"], "r") as file:
                demand = file.read()
            if "Modelica.Utilities.Files.loadResource" not in demand:
                raise ValueError("Demand template does not contain loadResource function. Current simulation setup aims to link demands to ressources but template does not support this."
                                "Check demand template for 'Modelica.Utilities.Files.loadRessources.")
            else:
                # Update attributes for non-supply heating nodes
                for node in uesgraph.nodelist_building:
                    if not uesgraph.node[node]["is_supply_heating"]:
                        uesgraph.nodes[node]["fileNameHeat"] = True
                        uesgraph.nodes[node]["fileNameCool"]=True
                        uesgraph.nodes[node]["fileNameDHW"]=True
                return uesgraph

    except KeyError:
        raise KeyError("'link_demands_to_ressources' not found in setup parameters. Set to True or False to link demands to ressources.") 
    except ValueError as e:
        raise e
    except Exception as e:
        raise Exception(f"Error processing link_demands_to_ressources: {e}")


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

def load_simulation_settings(sim_setup_path) -> dict:
    try:
        df = pd.read_excel(sim_setup_path,nrows=0)
        if "Version" in df.columns[0]:
            version = float(str(df.columns[0].split(":")[1].strip()))
            if version == 2.0:
                sim_setup = pd.read_excel(sim_setup_path,
                                        header =1,
                                        skiprows=[2,3],
                                        )
                sim_setup = sim_setup.drop(columns="Parameter:")
        else:
            sim_setup = pd.read_excel(sim_setup_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Excel file not found {sim_setup_path}")
    if len(sim_setup.index) == 0:
        raise ValueError("Excel file is empty")
        
    simulation_dict = sim_setup.to_dict(orient="records")
    return simulation_dict

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
