
import os
import datetime
import pandas as pd
import json
from uesgraphs.DHW_estimation import OpenDHW

import logging
import tempfile
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

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{name}{timestamp}.log")
    print(f"Logfile findable here: {log_file}")

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logger.propagate = False

    return logger

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

## Helper functions
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
        logger = set_up_logger(f"{__name__}.load_simulation_settings_from_excel")

    sim_params = _load_excel(excel_path, 'Simulation', logger)

    # Validate required simulation parameters
    required = ['timestep','stop_time']
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
    
def create_profiles(info_path, 
                    timestep, 
                    mean_drawoff_vol_per_day,
                    temp_dT_dhw,
                    holidays= OpenDHW.get_holidays(country_code = "DE", year = 2025),
                    logger=None):
    """Create DHW profiles according to infos in geojson.

    Parameters
    ----------
    info_path : path
        Full path to json with building infos.
    timestep : int
        Timestep in seconds for the generated time-series.
    holidays : list of datetime.date, optional
        List of holiday dates to consider in the profile generation (default: German holidays for 2025).
    mean_drawoff_vol_per_day : float
        Average drawoff volume per day in liters per occupant
    logger : logging.Logger, optional
        Logger instance for logging progress and warnings (default: None, creates a new logger if not provided).

    Returns
    -------
    pd.DataFrame
        DataFrame containing the generated DHW profiles for each building
    """
    district_file = info_path       
    
    if not os.path.exists(district_file):
        raise FileNotFoundError(f"District file not found: {district_file}")
    
    with open(district_file) as json_file:
        geojson = json.load(json_file)

    building_info = geojson.get("features", [])

    logger.info(f"Processing {len(building_info)} buildings...")

    df = None
    
    successful_buildings = 0
    for i in range(0,len(building_info)):
        try:
            bldg_info = building_info[i]["properties"]
            if i % 5 == 0 or i <= 10:  # More frequent feedback
                logger.info(f"  Processing building {i}/{len(building_info)}: {bldg_info['name']}")
                
            # Map archetype to OpenDHW types
            archetype = bldg_info["archetype"]
            
            if archetype in ["OfficeExisting", "OfficeWithDataCenter", "OfficeHighRise", "OfficeHighRiseKita"]:
                # generate time-series with OpenDHW
                timeseries_df = OpenDHW.generate_dhw_profile(
                    s_step=timestep,
                    categories=4,
                    occupancy=bldg_info["occupants"],
                    building_type="OB",
                    weekend_weekday_factor=1,
                    holidays=holidays,
                    mean_drawoff_vol_per_day=mean_drawoff_vol_per_day,
                )
                timeseries_df = OpenDHW.compute_heat(
                    timeseries_df=timeseries_df,
                    temp_dT=temp_dT_dhw
                )
            elif archetype in ["MultiFamilyHouse"]:
                # generate time-series with OpenDHW
                timeseries_df = OpenDHW.generate_dhw_profile(
                    s_step=timestep,
                    categories=4,
                    occupancy=bldg_info["occupants"],
                    building_type="MFH",
                    weekend_weekday_factor=1.2,
                    holidays=holidays,
                    mean_drawoff_vol_per_day=mean_drawoff_vol_per_day,
                )
                timeseries_df = OpenDHW.compute_heat(
                    timeseries_df=timeseries_df,
                    temp_dT=temp_dT_dhw
                )
            elif archetype in ["SingleFamilyHouse"]:
                # generate time-series with OpenDHW
                timeseries_df = OpenDHW.generate_dhw_profile(
                    s_step=timestep,
                    categories=4,
                    occupancy=bldg_info["occupants"],
                    building_type="SFH",
                    weekend_weekday_factor=1.2,
                    holidays=holidays,
                    mean_drawoff_vol_per_day=mean_drawoff_vol_per_day,
                )
                timeseries_df = OpenDHW.compute_heat(
                    timeseries_df=timeseries_df,
                    temp_dT=temp_dT_dhw
                )
            else:
                logger.info(f"  Warning: Unknown archetype '{archetype}' for building '{bldg_info['name']}' - skipping")
                continue
                
            successful_buildings += 1

            if isinstance(timeseries_df, pd.DataFrame):
                if "Heat_W" not in timeseries_df.columns:
                    raise KeyError(f"'Heat_W' not found in columns: {timeseries_df.columns}")
                    
                series = timeseries_df["Heat_W"]
            else:
                raise TypeError("timeseries_df is not a DataFrame as expected")

            series.name = bldg_info["name"]

            df = pd.concat([df, series], axis=1) if df is not None else series.to_frame()
                    
        except Exception as e:
            logger.info(f"  Warning: Could not process building '{i}': {e}")
            continue
    
    logger.info(f"Successfully created {successful_buildings}/{len(building_info)} buildings")
    
    return df

def generate_DHW_profiles_from_geojson(buildings_info_path, save_path, 
                    timestep=3600,
                    mean_drawoff_vol_per_day=40,
                    temp_dT_dhw=35, 
                    sim_setup_path=None, 
                    logger=None,
                    log_level=logging.DEBUG
                    ):
    """
    Run OpenDHW for demand estimation based on building information from a .geojson file.

    Parameters:
    -----------
    buildings_info_path : str
        The path to the .geojson file containing building information for TEASER model creation.
    save_path : str or Path
        Directory path where the resulting demand CSV files will be saved.
    timestep : int, optinal
        Simulation timestep in seconds (default is 3600 for hourly data)
    mean_drawoff_vol_per_day : float, optional
        Average drawoff volume per day in liters per occupant (default is 40 L/day/occupant)
    temp_dT_dhw : float, optional
        Temperature difference for Heat calculation from mass flows in K (default is 35 K)
    sim_setup_path : str or Path, optional
        Path to the simulation setup for timestep and stop time. If not provided, default values will be used.
    logger : logging.Logger, optional
        Logger instance. If None, creates a new file logger in temp directory
    log_level : int, optional
        Logging level (default is logging.DEBUG). Only used if logger is None

    Returns:
    --------
    tuple
        Paths to the generated demand CSV files: (heating_demand_csv, cooling_demand_csv)

    """
    
    if logger is None:
        logger = set_up_file_logger("OpenDHWRun", level=int(log_level))

    # Step 0: Load simulation settings

    if sim_setup_path is not None:
        try:
            sim_params = load_simulation_settings_from_excel(sim_setup_path, logger)
            timestep = int(sim_params.get('timestep', timestep))
            mean_drawoff_vol_per_day = float(sim_params['mean_drawoff_vol_per_day'])
            temp_dT_dhw = float(sim_params['temp_dT_dhw'])
            logger.info(f"Loaded simulation settings from Excel: timestep={timestep}")
        except Exception as e:
            logger.warning(f"Could not load simulation settings from Excel: {e}. Using default values.")

    timesteps = int(365*24*3600/ timestep)
    index = pd.date_range(
        datetime.datetime(2025, 1, 1),
        periods=timesteps,
        freq=f"{int(timestep/3600)}h"
    )

    demand_csv_path = os.path.join(save_path, "demand_csv")
    if not os.path.exists(demand_csv_path):
        os.makedirs(demand_csv_path)

    # Step 1: Create DHW profiles

    dhw = create_profiles(buildings_info_path, timestep, mean_drawoff_vol_per_day, temp_dT_dhw, logger=logger)

    if len(dhw) != len(index):
        logger.warning("Length mismatch between DHW data and index")
    else:
        dhw.index = index
    
    # Step 2: Save to CSV

    dhw.to_csv(os.path.join(demand_csv_path, "demands-dhw.csv"), index= True)

    return os.path.join(demand_csv_path, "demands-dhw.csv")