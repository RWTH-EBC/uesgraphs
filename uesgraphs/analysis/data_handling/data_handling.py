
import pyarrow.parquet as pq

import pandas as pd

import re
from typing import List, Dict, Generator, Optional, Union, Tuple, Set
import os
import pathlib as Path

import logging
import tempfile
from datetime import datetime


#### Global Variables ####
MASKS = None  # Dictionary to store masks for column names


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
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    print(f"Logfile findable here: {log_file}")
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    logger.propagate = False
    
    return logger

#### Functions 2: Data Aquisition ####


def check_input_file(file_path: str, logger=None) -> str:
    """
    Check and prepare input file for processing.
    
    Handles different file formats and converts .mat files to .gzip if needed.
    
    Args:
        file_path: Path to the input file
        
    Returns:
        Path to the processed file (usually .gzip format)
        
    Raises:
        ValueError: If file doesn't exist or conversion fails
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.check_input_file")

    if not file_path:
        raise ValueError("File path cannot be empty")

    base_path = os.path.splitext(file_path)[0]
    gzip_path = f"{base_path}.gzip"

    # Check for gzip first (preferred format)
    if os.path.exists(gzip_path):
        logger.info(f"Found existing gzip file: {gzip_path}")
        return gzip_path
    
    # Check for .mat file and convert
    mat_path = f"{base_path}.mat"
    if os.path.exists(mat_path):
        try:
            logger.info(f"Converting .mat file to parquet: {mat_path}")
            gzip_new = mat_to_parquet(save_as=base_path, fname=mat_path, with_unit=False)
            logger.info(f"Successfully converted .mat file to: {gzip_new}")
            return gzip_new
        except Exception as e:
            logger.error(f"Failed to convert .mat file: {mat_path}")
            raise ValueError(f"Could not convert .mat file to parquet: {mat_path}") from e
    
    # Finally check if original file exists
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    
    logger.info(f"Using original file: {file_path}")
    return file_path


def validate_columns_exist(file_path: str, required_columns: List[str],
                          logger: Optional[logging.Logger] = None) -> Set[str]:
    """
    Check if all required columns exist in the simulation data file.
    
    Args:
        file_path: Path to the parquet/simulation file
        required_columns: List of exact column names that must exist
        logger: Logger instance (optional)
        
    Returns:
        Set of available columns from the file
        
    Raises:
        KeyError: If any required columns are missing
        ValueError: If file cannot be read
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.validate_columns_exist")
    
    logger.info(f"Validating {len(required_columns)} required columns in: {file_path}")
    
    # Read file metadata (no data loading)
    try:
        parquet_file = pq.ParquetFile(file_path)
        available_columns = set(parquet_file.schema.names)
        logger.debug(f"File contains {len(available_columns)} total columns")
    except Exception as e:
        error_msg = f"Could not read file metadata: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Check for missing columns
    required_set = set(required_columns)
    missing_columns = required_set - available_columns
    
    if missing_columns:
        missing_list = sorted(missing_columns)
        error_msg = f"Missing required columns: {missing_list}"
        logger.error(error_msg)
        
        # Raise KeyError with first missing column for auto-retry compatibility
        first_missing = missing_list[0]
        raise KeyError(first_missing)
    
    logger.info("✅ All required columns found in data file")
    return available_columns

def process_simulation_result(file_path: str, filter_list: List[str], 
                        chunk_size: int = 100000, logger=None) -> Generator[pd.DataFrame, None, None]:
    """
    Process a parquet file in chunks to reduce memory usage.
    
    Args:
        file_path: Path to the parquet file
        filter_list: List of column patterns to filter
        chunk_size: Number of rows to process at once
        logger: Optional logger instance
        
    Yields:
        pd.DataFrame: Processed chunks of the parquet file
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.process_parquet_file")
    
    # Step 1: Check if file exists and is valid
    check_input_file(file_path=file_path, logger=logger)

    # Step 1: Validate all columns exist (will raise KeyError if missing)
    available_columns = validate_columns_exist(file_path, required_columns=filter_list, logger=logger)
    
    # Step 2: Check if any columns match the filter_list
    logger.info(f"Starting parquet file processing: {file_path}")
    logger.debug(f"Filter patterns: {filter_list}")
    logger.debug(f"Chunk size: {chunk_size}")
    
    try:
        # Read parquet file metadata to get columns
        parquet_file = pq.ParquetFile(file_path)
        chunks = []
        total_rows = 0
       
        
        # Read and process the file in chunks
        for batch in parquet_file.iter_batches(batch_size=chunk_size, columns=filter_list):
            total_rows += 1
            chunk_df = batch.to_pandas()
            chunks.append(chunk_df)
            if len(chunks) % 10 == 0:  # Log every 10 chunks
                logger.debug(f"Loaded {len(chunks)} chunks, {total_rows} rows so far")

        if not chunks:
            logger.warning("No data loaded from file")
            return pd.DataFrame()
        
        result_df = pd.concat(chunks, axis = 0, ignore_index=True)
        
        logger.info(f"Successfully loaded {len(result_df)} rows, {len(result_df.columns)} columns")
        logger.debug(f"DataFrame memory usage: {result_df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")
        return result_df
    except Exception as e:
        logger.error(f"Error processing parquet file {file_path}: {str(e)}")
        raise e



#### Functions 3: Data Processing ####

def prepare_DataFrame(df, base_date=datetime(2024, 1, 1), time_interval="15min", 
                      start_date=None, end_date=None, logger=None) -> pd.DataFrame:
    """
    Prepare a DataFrame with a datetime index using customizable parameters.
    
    Parameters:
    -----------
    df : pandas.DataFrame
        The DataFrame to be processed
    base_date : datetime, optional
        The starting date for the index (default: 2024-01-01)
    time_interval : str, optional
        Frequency of the time intervals (e.g., '15min', '1h', '30min', default: '15min')
    start_date : datetime, optional
        If provided, slice the DataFrame from this date (inclusive)
    end_date : datetime, optional
        If provided, slice the DataFrame until this date (inclusive)
    logger : logging.Logger, optional
        Logger instance for logging operations
    
    Returns:
    --------
    DataFrame: A DataFrame containing the data from the parquet file for the specified time period.
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.prepare_DataFrame")
    
    logger.info(f"Preparing DataFrame with {len(df)} rows and {len(df.columns)} columns")
    logger.debug(f"Parameters - base_date: {base_date}, time_interval: {time_interval}")
    logger.debug(f"Date filtering - start_date: {start_date}, end_date: {end_date}")
    
    try:
        # Create datetime index with specified frequency    
        logger.debug(f"Creating datetime index with frequency '{time_interval}'")
        datetime_index = pd.date_range(start=base_date, periods=len(df), freq=time_interval)
        logger.debug(f"Created datetime index from {datetime_index[0]} to {datetime_index[-1]}")
        
        # Set the index of the DataFrame to the datetime index
        df.index = datetime_index
        df.index.name = 'DateTime'
        logger.info(f"Applied datetime index to DataFrame")
        
        # Filter by date range if specified
        original_length = len(df)
        if start_date is not None and end_date is not None:
            logger.info(f"Filtering DataFrame from {start_date} to {end_date}")
            df = df.loc[start_date:end_date]
        elif start_date is not None:
            logger.info(f"Filtering DataFrame from {start_date} onwards")
            df = df.loc[start_date:]
        elif end_date is not None:
            logger.info(f"Filtering DataFrame up to {end_date}")
            df = df.loc[:end_date]
        
        # Log filtering results if any filtering was applied
        if len(df) != original_length:
            logger.info(f"Date filtering applied: {original_length} → {len(df)} rows ({len(df)/original_length*100:.1f}% retained)")
            if len(df) == 0:
                logger.warning("Date filtering resulted in empty DataFrame - check date range parameters")
        else:
            logger.debug("No date filtering applied")
        
        logger.info(f"Successfully prepared DataFrame: {len(df)} rows, index range: {df.index[0]} to {df.index[-1]}")
        return df
        
    except ValueError as e:
        error_msg = f"Error creating date range with frequency {time_interval} and base date {base_date}. Original error: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e
    except Exception as e:
        error_msg = f"Unexpected error in prepare_DataFrame: {str(e)}"
        logger.error(error_msg)
        raise


# Configuration Dictionary für alle bekannten AixLib Versionen
AIXLIB_MASKS = {
    "2.1.0": {
        "m_flow": "networkModel.pipe{pipe_code}{type}.port_a.m_flow",
        "dp": "networkModel.pipe{pipe_code}{type}.dp",
        "p_a": "networkModel.pipe{pipe_code}{type}.port_a.p",
        "p_b": "networkModel.pipe{pipe_code}{type}.port_b.p",
        "T_a": "networkModel.pipe{pipe_code}{type}.sta_a.T",
        "T_b": "networkModel.pipe{pipe_code}{type}.sta_b.T",
    },
    "2.0.0": {
        "m_flow": "networkModel.pipe{pipe_code}{type}.port_a.m_flow",
        "p_a": "networkModel.pipe{pipe_code}{type}.port_a.p",
        "p_b": "networkModel.pipe{pipe_code}{type}.ports_b[1].p",
        "T_a": "networkModel.pipe{pipe_code}{type}.sta_a.T",
        "T_b": "networkModel.pipe{pipe_code}{type}.sta_b[1].T",
    }
}

def get_MASKS(aixlib_version: str, logger: Optional[logging.Logger] = None) -> Dict[str, str]:
    """
    Returns the correct variable masks for different AixLib versions.
    
    The naming convention for variables in the simulation model depends on the AixLib version
    used to build it. The key difference is in how ports are referenced:
    - Version 2.1.0: Uses direct port access (e.g., port_b.p)
    - Earlier versions: Uses array indexing for ports_b (e.g., ports_b[1].p)
    
    Args:
        aixlib_version: Version string of AixLib used to build the model
        logger: Logger instance (optional)
        
    Returns:
        Dictionary mapping variable types to their full path in the simulation model
        
    Raises:
        ValueError: If the specified version is not supported
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.get_MASKS")
    
    if aixlib_version not in AIXLIB_MASKS:
        available_versions = list(AIXLIB_MASKS.keys())
        error_msg = (f"AixLib version '{aixlib_version}' not supported. "
                    f"Available versions: {available_versions}")
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Using AixLib version {aixlib_version} masks")
    return AIXLIB_MASKS[aixlib_version].copy()


def check_supply_type(graph, logger: Optional[logging.Logger] = None):
    """
    Check and validate the supply type of the graph.
    
    Args:
        graph: UESGraph instance
        logger: Logger instance (optional)
        
    Returns:
        str: Supply type ("supply" or "return")
        
    Raises:
        ValueError: If supply_type is missing or invalid
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.check_supply_type")
    
    if "supply_type" not in graph.graph:
        error_msg = "The graph does not have a supply_type attribute"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    supply_type = graph.graph["supply_type"]
    if supply_type not in ["supply", "return"]:
        error_msg = f"The graph supply_type attribute must be either 'supply' or 'return', got: {supply_type}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Graph supply type: {supply_type}")
    return supply_type

def assign_simulation_data(graph, sim_data, start_date, end_date, 
                           aixlib_version: str = "2.1.0", 
                           time_interval: str = "15min",
                           auto_retry: bool = True,
                           validate_network: bool = False,
                           log_dir: Optional[str] = None) -> any:
    """
    Assign simulation data to UESGraph with automatic version retry and network validation.
    
    Args:
        graph: UESGraph instance
        sim_data: Path to simulation data file
        start_date: Start date for data processing  
        end_date: End date for data processing
        aixlib_version: AixLib version to use (default: "2.1.0")
        time_interval: Time interval for data processing (default: "15min")
        auto_retry: Whether to automatically retry with different version on error (default: True)
        validate_network: Whether to validate network compatibility (default: True)
        log_dir: Directory for log files (optional)
        
    Returns:
        UESGraph with assigned simulation data
        
    Raises:
        ValueError: If network validation fails
        KeyError: If data assignment fails and auto_retry is disabled
    """
    # Set up file logger for this major function
    logger = set_up_file_logger(f"{__name__}.assign_data_to_uesgraphs", 
                               log_dir=log_dir, level=logging.DEBUG)
    
    logger.info("="*60)
    logger.info("Starting UESGraph data assignment process")
    logger.info(f"Graph: {graph.graph.get('name', 'unnamed')}")
    logger.info(f"Simulation data: {sim_data}")
    logger.info(f"Period: {start_date} to {end_date}")
    logger.info(f"AixLib version: {aixlib_version}")
    logger.info(f"Auto-retry: {auto_retry}")
    logger.info(f"Validate network: {validate_network}")
    logger.info("="*60)
    
    def build_filter_list(graph, version: str, logger: Optional[logging.Logger] = None) -> List[str]:
        """        Build a list of variable names to filter from the graph edges based on the AixLib version.
        """
        if logger is None:
            logger = set_up_terminal_logger(f"{__name__}.build_filter_list")
        
        # Check supply type
        supply_type = check_supply_type(graph, logger=logger)
        supply_type_prefix = {"supply": "", "return": "R"}
        
        # Get masks for this version
        masks = get_MASKS(version, logger=logger)
        
        # Build filter list for data extraction
        filter_list = []
        for edge in graph.edges:
            pipe_code = graph.edges[edge]["name"]
            for mask_type, mask_pattern in masks.items():
                var_name = mask_pattern.format(
                    pipe_code=pipe_code, 
                    type=supply_type_prefix[supply_type]
                )
                filter_list.append(var_name)
        return filter_list

    def _attempt_assignment(version: str) -> any:
        """Internal helper to attempt data assignment with specific version."""
        logger.info(f"Attempting data assignment with AixLib version {version}")
        check_input_file(file_path=sim_data, logger=logger)

           
        # Build filter list based on the graph and version
        filter_list = build_filter_list(graph, version, logger=logger)
        logger.debug(f"Filter list for version {version}: len{filter_list}")        
        try:
            validate_columns_exist(file_path=sim_data, required_columns=filter_list, logger=logger)
        except KeyError as e_key:
            logger.warning(f"KeyError during data assignment: {e_key}")
            retry_version = None
            versions = list(AIXLIB_MASKS.keys())
            for v in versions:
                if v == version:
                    continue
                try:
                    logger.info(f"Auto-retrying with AixLib version {retry_version}")
                    filter_list = build_filter_list(graph, v, logger=logger)
                    validate_columns_exist(sim_data, filter_list, logger=logger)
                    retry_version = v
                    break
                except KeyError as retry_error:
                    logger.error(f"Retry with version {v} failed: {retry_error} Check if json file and sim_data belong to same network")
                    raise KeyError(f"Failed to validate columns with any supported version: {versions}. Check if json file and sim_data belong to same network") from retry_error

        # Process simulation data
        df = process_simulation_result(file_path=sim_data, filter_list=filter_list, logger=logger)
        logger.info(f"Raw data shape: {df.shape}")
        
        # Prepare DataFrame with time index
        df = prepare_DataFrame(df, start_date=start_date, end_date=end_date, 
                             time_interval=time_interval, logger=logger)
        logger.info(f"Processed data shape: {df.shape}")
        
        # Optional network validation
        if validate_network:
            from .network_validation import validate_network_compatibility
            validation_results = validate_network_compatibility(
                graph, df.columns.tolist(), version, logger=logger
            )
            logger.info(f"Network validation passed: {validation_results['compatibility_score']:.1%} compatibility")
        
        # Assign node values (pressure and temperature)
        logger.info("Assigning node values (pressure and temperature)")
        graph_with_nodes = get_node_values(graph, df.iloc[0], 
                                         pipe_type=supply_type_prefix[supply_type],
                                         logger=logger)
        
        # Assign time series data to nodes
        logger.info("Assigning time series data to nodes")
        for node in graph_with_nodes.nodes:
            press_var = graph_with_nodes.nodes[node]["press_name"]
            temp_var = graph_with_nodes.nodes[node]["temp_name"]
            
            graph_with_nodes.nodes[node]["press_flow"] = df[press_var]
            graph_with_nodes.nodes[node]["temperature_supply"] = df[temp_var]
            
            logger.debug(f"Node {node}: pressure={press_var}, temperature={temp_var}")
        
        # Assign time series data to edges
        logger.info("Assigning time series data to edges")
        for edge in graph_with_nodes.edges:
            pipe_name = graph_with_nodes.edges[edge]["name"]
            type_suffix = supply_type_prefix[supply_type]
            
            # Mass flow
            m_flow_var = masks["m_flow"].format(pipe_code=pipe_name, type=type_suffix)
            graph_with_nodes.edges[edge]["m_flow"] = df[m_flow_var]
            
            # Pressure drop
            if "dp" in masks:
                dp_var = masks["dp"].format(pipe_code=pipe_name, type=type_suffix)
                graph_with_nodes.edges[edge]["press_drop"] = abs(df[dp_var])
            
            logger.debug(f"Edge {edge} (pipe {pipe_name}): m_flow={m_flow_var}")
        
        logger.info(f"✅ Data assignment successful with AixLib version {version}")
        return graph_with_nodes
    
    # First attempt with specified version
    result = _attempt_assignment(aixlib_version)
    logger.info("="*60)
    logger.info("UESGraph data assignment completed successfully")
    logger.info("="*60)
    return result
      
# Convenience function um neue Versionen hinzuzufügen
def add_aixlib_version(version, masks):
    """
    Add support for a new AixLib version.
    
    Args:
        version: Version string (e.g., "2.2.0")
        masks: Dictionary with mask definitions
    """
    required_keys = {"m_flow", "p_a", "p_b", "T_a", "T_b"}
    if not required_keys.issubset(set(masks.keys())):
        missing = required_keys - set(masks.keys())
        raise ValueError(f"Missing required mask keys: {missing}")
    
    AIXLIB_MASKS[version] = masks
    print(f"Added support for AixLib version {version}")


def list_supported_versions():
    """List all supported AixLib versions."""
    return list(AIXLIB_MASKS.keys())