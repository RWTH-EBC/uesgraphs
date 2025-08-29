
import pyarrow.parquet as pq

import pandas as pd


from typing import List, Dict, Generator, Optional, Union, Tuple, Set, Any
import os
from pathlib import Path

import logging
import tempfile
from datetime import datetime

import uesgraphs as ug
from uesgraphs.systemmodels import utilities as ut
from uesgraphs.analysis.data_handling import graph_transformation


#### Global Variables ####
AIXLIB_MASKS = None  # Dictionary to store masks for column names


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

#### Functions 4: Data Assignment to UESGraph ####

AIXLIB_MASKS = {
    "2.1.0": {
        "edge": {
            # Extensive properties - same value at both ports
            "m_flow": "networkModel.pipe{pipe_code}{type}.port_a.m_flow",
            "dp": "networkModel.pipe{pipe_code}{type}.dp",
        },
        "node": {
            # Intensive properties - may differ between ports
            "pressure": {
                "port_a": "networkModel.pipe{pipe_code}{type}.port_a.p",
                "port_b": "networkModel.pipe{pipe_code}{type}.port_b.p"
            },
            "temperature": {
                "port_a": "networkModel.pipe{pipe_code}{type}.sta_a.T", 
                "port_b": "networkModel.pipe{pipe_code}{type}.sta_b.T"
            }
        }
    },
    "2.0.0": {
        "edge": {
            # Extensive properties - same value at both ports
            "m_flow": "networkModel.pipe{pipe_code}{type}.port_a.m_flow",
        },
        "node": {
            # Intensive properties - may differ between ports
            "pressure": {
                "port_a": "networkModel.pipe{pipe_code}{type}.port_a.p",
                "port_b": "networkModel.pipe{pipe_code}{type}.ports_b[1].p"
            },
            "temperature": {
                "port_a": "networkModel.pipe{pipe_code}{type}.sta_a.T",
                "port_b": "networkModel.pipe{pipe_code}{type}.sta_b[1].T"
            }
        }
    }
}

def build_filter_list_pipe(graph, mask, logger=None):
    """
    Build a list of filter variables for pipes in a district heating network graph.
    
    This function extracts patterns from a mask data structure and formats them
    with specific pipe codes and type information for each edge (pipe) in the graph.
    This is useful for filtering and analyzing district heating networks.
    
    Args:
        graph : uesgraphs object.
        mask (dict): Hierarchical data structure containing filter patterns.
                    Expected categories are 'edge' and 'node':
                    - 'edge': Dict with direct pattern values
                    - 'node': Dict with nested pattern values
        logger (logging.Logger, optional): Logger instance for debug output.
                                          Will be created automatically if None.
    
    Returns:
        list: List of formatted variable names for all pipes in the graph,
              based on the mask patterns.
    
    Example:
        >>> mask = {
        ...     'edge': {'pressure': 'p_{pipe_code}_{type}'},
        ...     'node': {'inlet': {'temp': 'T_in_{pipe_code}_{type}'}}
        ... }
        >>> filter_list = build_filter_list_pipe(graph, mask)
        >>> print(filter_list)
        ['p_PIPE001_supply', 'T_in_PIPE001_supply', ...]
    
    Raises:
        KeyError: If pipe edges don't have a 'name' attribute
        AttributeError: If graph doesn't have edges attribute
    """
    # Initialize logger if not provided
    if logger is None:
        logger = set_up_terminal_logger("BuildFilterListPipe")
    
    # Collection of all simulation patterns from the mask structure
    simulation_patterns = []
    
    # Iterate through all categories in the mask
    for category_name, category_data in mask.items():
        if category_name not in ["edge", "node"]:
            logger.warning(f"Unknown category '{category_name}' in mask, skipping")
            continue
            
        if category_name == "edge":
            # Edge category: direct extraction of pattern values
            # Example: {'m_flow': 'p_{pipe_code}_{type}'} -> ['p_{pipe_code}_{type}']
            simulation_patterns.extend(category_data.values())
            logger.debug(f"Added {len(category_data)} edge patterns")
            
        elif category_name == "node":
            # Node category: nested structure - extract all port patterns
            # Example: {'temperature': {'port_a': 'T_in_{pipe_code}_{type}'}} 
            #          -> ['T_in_{pipe_code}_{type}']
            for port_name, attribute_patterns in category_data.items():
                if isinstance(attribute_patterns, dict):
                    simulation_patterns.extend(attribute_patterns.values())
                    logger.debug(f"Added {len(attribute_patterns)} node patterns "
                               f"for port '{port_name}'")
                else:
                    logger.warning(f"Expected dict for node port '{port_name}', "
                                 f"got {type(attribute_patterns)}")
    
    logger.info(f"Extracted {len(simulation_patterns)} simulation patterns total")
    
    # Get type prefix from graph (e.g., 'supply', 'return')
    type_prefix = get_supply_type_prefix(graph)
    logger.debug(f"Using type prefix: '{type_prefix}'")
    
    # List for all generated filter variables
    filter_variables = []
    
    # Generate filter variables for each edge (pipe) in the graph
    for edge in graph.edges:
        try:
            # Extract pipe code from edge attributes
            pipe_code = graph.edges[edge]["name"]
            
            # Generate a variable for each simulation pattern
            for pattern in simulation_patterns:
                # Format pattern with specific values
                variable_name = pattern.format(
                    pipe_code=pipe_code,
                    type=type_prefix
                )
                filter_variables.append(variable_name)
                
            logger.debug(f"Generated {len(simulation_patterns)} variables "
                        f"for pipe '{pipe_code}'")
                        
        except KeyError as e:
            logger.error(f"Edge {edge} missing required attribute: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing edge {edge}: {e}")
            raise
    
    logger.info(f"Created filter list with {len(filter_variables)} entries "
               f"for {len(graph.edges)} pipes")
    
    return filter_variables


##### Assign node values

def assign_node_values(graph, df, port_mapping, mask, time_index=0, logger=None):
    """
    Assigns node values from simulation data using flexible mask configuration.
    
    Processes intensive properties (pressure, temperature) that may differ between 
    ports of the same pipe, unlike extensive properties (mass flow) that are 
    identical at both ports.
    
    Args:
        graph: NetworkX or uesgraphs graph with nodes to assign values to
        df: DataFrame containing simulation data
        port_mapping: Dict mapping node_ids to list of connected ports.
                     Example: {1: ['pipe001.port_a', 'pipe002.port_b'], 
                              2: ['pipe001.port_b', 'pipe003.port_a']}
                     Source: [Method name if known, otherwise leave empty]
        mask: Mask dictionary containing node configuration for intensive properties
        time_index: Time step index to extract from df (default: 0)
        logger: Logger instance (optional, creates terminal logger if None)
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.assign_node_values")
    
    # Extract node configuration
    node_config = mask.get("node", {})
    if not node_config:
        logger.error("No 'node' configuration found in mask")
        return
    
    type_suffix = get_supply_type_prefix(graph)
    
    stats =  {
        'processed_count': 0,
        'inconsistency_count': 0, 
        'pattern_conflicts': 0
    }
    
    for node_id, node_ports in port_mapping.items():
        if not node_ports:
            continue
            
        _assign_attributes_to_node(
            graph, node_id, node_ports, df, node_config,
            type_suffix, stats, logger
        )
        
        stats['processed_count'] += 1
    
    logger.info(f"Assignment completed:")
    logger.info(f"  Processed nodes: {stats['processed_count']}")
    logger.info(f"  Within-pattern inconsistencies: {stats['inconsistency_count']}")
    logger.info(f"  Cross-pattern conflicts: {stats['pattern_conflicts']}")

def _assign_attributes_to_node(graph, node_id, node_ports, df, config, 
                              type_suffix, stats, logger):
    """Assign all attributes to a single node.
        config: {"attribute": {"port_suffix": "pattern_with_{pipe_code}"}}
                ex.: {"temperature": {"port_a": "networkModel.pipe{pipe_code}{type}.sta_a.T"}}
    """
    
    for attribute_name, port_patterns in config.items():
        """Collect values for a specific attribute from all relevant ports.
        attribute_name: e.g. "temperature"
        port_patterns: e.g. {"port_a": "networkModel.pipe{pipe_code}{type}.sta_a.T",
                        "port_b": "networkModel.pipe{pipe_code}{type}.sta_b.T"}
        """
        series_list = []
        for port in node_ports:
            
            pipe_name, port_suffix = _parse_port_identifier(port)
            if port_suffix in port_patterns:
                pattern = port_patterns[port_suffix]
                column_name = pattern.format(pipe_code=pipe_name, type=type_suffix)
            
                if column_name in df.columns:
                    series = df[column_name]
                    series_list.append(series)
                else:
                    logger.debug(f"Column not found: {column_name}")

        if len(series_list) == 0:
            logger.debug(f"No data found for {attribute_name} at node {node_id}")
            continue

        # Check if all series are identical
        if len(series_list) > 1:
            all_equal = all(series_list[0].equals(series) for series in series_list[1:])
            if not all_equal:
                logger.warning(f"Node {node_id}: Inconsistent {attribute_name} time series found")
                stats['inconsistency_count'] += 1
        
        # Use first series as result
        graph.nodes[node_id][attribute_name] = series_list[0]        

def _parse_port_identifier(port):
    """Parse port identifier to extract pipe name and port suffix."""
    port_parts = port.split(".")
    if len(port_parts) < 2:
        raise ValueError(f"Invalid port format: {port}. Expected 'pipe_name.port_suffix'")
    return port_parts[0].replace("pipe", ""), port_parts[1]

##### Assign edge data

def assign_edge_data(graph, MASK, df):
    type_suffix = get_supply_type_prefix(graph)
    for edge in graph.edges:
        for edge_variable, variable_mask in MASK["edge"].items():
            pipe_name = graph.edges[edge]["name"]
            variable_name = variable_mask.format(pipe_code=pipe_name, type=type_suffix)
            graph.edges[edge][edge_variable] = df[variable_name]
        
##### Validation functions

def validate_edge_attributes(graph, edge_attributes, reference_df, logger=None):
    """
    Validates graph edge attributes against a reference DataFrame.
    
    Checks if the length of attribute arrays in edges matches the 
    number of rows in the reference DataFrame.
    
    Args:
        graph: uesgraphs
        edge_attributes (dict): Dictionary containing edge attributes to validate
        reference_df (pd.DataFrame): Reference DataFrame for length comparison
        logger (logging.Logger, optional): Logger instance. If None, a 
                                         terminal logger will be created.
    
    Returns:
        bool: True if all validations pass, False otherwise
        
    Raises:
        ValueError: For critical validation errors
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.validate_edge_attributes")
    
    logger.info("Starting edge attribute validation...")
    
    expected_length = reference_df.shape[0]
    validation_passed = True
    errors = []
    
    # Validate edge attributes
    logger.info(f"Validating edge attributes for {len(graph.edges)} edges...")
    
    if edge_attributes:
        for edge_idx, edge in enumerate(graph.edges):
            for edge_attr in edge_attributes.keys():
                if edge_attr in graph.edges[edge]:
                    actual_length = len(graph.edges[edge][edge_attr])
                    
                    if actual_length != expected_length:
                        error_msg = (
                            f"Edge {edge} - Attribute '{edge_attr}': "
                            f"length {actual_length} != expected length {expected_length}"
                        )
                        logger.error(error_msg)
                        errors.append(error_msg)
                        validation_passed = False
                    else:
                        logger.debug(
                            f"Edge {edge} - Attribute '{edge_attr}': OK "
                            f"(length: {actual_length})"
                        )
                else:
                    warning_msg = f"Edge {edge} - Attribute '{edge_attr}' not found"
                    logger.warning(warning_msg)
    else:
        logger.warning("No edge attributes provided for validation")
    
    # Validation summary
    if validation_passed:
        logger.info("✓ Edge attribute validation completed successfully")
    else:
        logger.error(f"✗ Edge attribute validation failed: {len(errors)} errors")
        for error in errors[:5]:  # Show maximum 5 errors in summary
            logger.error(f"  - {error}")
        if len(errors) > 5:
            logger.error(f"  ... and {len(errors) - 5} more errors")
    
    return validation_passed

def validate_node_attributes(graph, node_attributes, reference_df, logger=None):
    """
    Validates graph node attributes against a reference DataFrame.
    
    Checks if the length of attribute arrays in nodes matches the 
    number of rows in the reference DataFrame.
    
    Args:
        graph: uesgraphs
        node_attributes (dict): Dictionary containing node attributes to validate
        reference_df (pd.DataFrame): Reference DataFrame for length comparison
        logger (logging.Logger, optional): Logger instance. If None, a 
                                         terminal logger will be created.
    
    Returns:
        bool: True if all validations pass, False otherwise
        
    Raises:
        ValueError: For critical validation errors
    """
    if logger is None:
        logger = set_up_terminal_logger(f"{__name__}.validate_node_attributes")
    
    logger.info("Starting node attribute validation...")
    
    expected_length = reference_df.shape[0]
    validation_passed = True
    errors = []
    
    # Validate node attributes
    logger.info(f"Validating node attributes for {len(graph.nodes)} nodes...")
    
    if node_attributes:
        for node_idx, node in enumerate(graph.nodes):
            for node_attr in node_attributes.keys():
                if node_attr in graph.nodes[node]:
                    actual_length = len(graph.nodes[node][node_attr])
                    
                    if actual_length != expected_length:
                        error_msg = (
                            f"Node {node} - Attribute '{node_attr}': "
                            f"length {actual_length} != expected length {expected_length}"
                        )
                        logger.error(error_msg)
                        errors.append(error_msg)
                        validation_passed = False
                    else:
                        logger.debug(
                            f"Node {node} - Attribute '{node_attr}': OK "
                            f"(length: {actual_length})"
                        )
                else:
                    warning_msg = f"Node {node} - Attribute '{node_attr}' not found"
                    logger.warning(warning_msg)
    else:
        logger.warning("No node attributes provided for validation")
    
    # Validation summary
    if validation_passed:
        logger.info("✓ Node attribute validation completed successfully")
    else:
        logger.error(f"✗ Node attribute validation failed: {len(errors)} errors")
        for error in errors[:5]:  # Show maximum 5 errors in summary
            logger.error(f"  - {error}")
        if len(errors) > 5:
            logger.error(f"  ... and {len(errors) - 5} more errors")
    
    return validation_passed


def assess_dp_quality(graph, 
                      negligible_abs_threshold=1.0, 
                      negligible_rel_threshold=0.001,
                      acceptable_abs_threshold=10.0, 
                      acceptable_rel_threshold=0.01):
    """
    Assesses the quality of node assignments based on pressure and pressure difference
    
    Parameters:
    -----------
    graph : uesgraph
        The district heating network graph object
    negligible_abs_threshold : float, default=1.0
        Absolute threshold for negligible deviations (Pa)
    negligible_rel_threshold : float, default=0.001
        Relative threshold for negligible deviations (0.1%)
    acceptable_abs_threshold : float, default=10.0
        Absolute threshold for acceptable deviations (Pa)
    acceptable_rel_threshold : float, default=0.01
        Relative threshold for acceptable deviations (1%)
    
    Returns:
    --------
    dict
        Dictionary with categories 'negligible', 'acceptable', 'investigate'
        and corresponding edges with timestamp information
    """
    stats = {
        'negligible': [],
        'acceptable': [], 
        'investigate': []
    }
    
    for edge in graph.edges:
        node1, node2 = list(edge)
        p1 = graph.nodes[node1]["pressure"]
        p2 = graph.nodes[node2]["pressure"]
        dp_calc = p1 - p2
        dp_sim = graph.edges[edge]["dp"]
        
        # Check for each timestamp
        for i in range(len(p1)):
            timestamp = p1.index[i] if hasattr(p1, 'index') else i
            
            abs_diff = abs(dp_calc.iloc[i] - dp_sim.iloc[i])
            rel_error = (abs_diff / abs(dp_sim.iloc[i]) 
                        if dp_sim.iloc[i] != 0 else float('inf'))
            
            edge_info = {
                'edge': edge,
                'timestamp': timestamp,
                'abs_diff': abs_diff,
                'rel_error': rel_error,
                'dp_calculated': dp_calc.iloc[i],
                'dp_simulated': dp_sim.iloc[i]
            }
            
            # Categorization based on thresholds
            if (abs_diff < negligible_abs_threshold or 
                rel_error < negligible_rel_threshold):
                stats['negligible'].append(edge_info)
                
            elif (abs_diff < acceptable_abs_threshold and 
                  rel_error < acceptable_rel_threshold):
                stats['acceptable'].append(edge_info)
                
            else:
                stats['investigate'].append(edge_info)
    
    return stats

def _format_dp_quality_summary(stats):
    """
    Formats a comprehensive summary of the pressure difference quality assessment as string.
    
    Parameters:
    -----------
    stats : dict
        Result from assess_dp_quality()
        
    Returns:
    --------
    str
        Formatted summary string ready for logging or printing
    """
    total_measurements = (len(stats['negligible']) + 
                         len(stats['acceptable']) + 
                         len(stats['investigate']))
    
    lines = []
    lines.append("=== Pressure Difference Quality Assessment ===")
    lines.append(f"Total measurements: {total_measurements}")
    lines.append(f"Negligible: {len(stats['negligible'])} ({len(stats['negligible'])/total_measurements*100:.1f}%)")
    lines.append(f"Acceptable: {len(stats['acceptable'])} ({len(stats['acceptable'])/total_measurements*100:.1f}%)")
    lines.append(f"Investigate: {len(stats['investigate'])} ({len(stats['investigate'])/total_measurements*100:.1f}%)")
    
    if stats['investigate']:
        lines.append("")
        lines.append("--- Critical Deviations (Top 5) ---")
        # Sort by absolute error
        worst_cases = sorted(stats['investigate'], 
                           key=lambda x: x['abs_diff'], reverse=True)[:5]
        
        for case in worst_cases:
            lines.append(f"Edge {case['edge']}, Time {case['timestamp']}: "
                        f"dp_sim={case['dp_simulated']:.2f} Pa, "
                        f"dp_calc={case['dp_calculated']:.2f} Pa, "
                        f"Diff={case['abs_diff']:.2f} Pa ({case['rel_error']*100:.2f}%)")
    
    return "\n".join(lines)


def _check_dp_quality_warnings(stats, logger=None):
    """
    Checks for critical pressure difference deviations and issues warnings.
    This may indicate faulty assignments in the network model.
    
    Parameters:
    -----------
    stats : dict
        Result from assess_dp_quality()
    logger : logging.Logger, optional
        Logger instance to use for warnings. If None, uses print statements.
        
    Returns:
    --------
    bool
        True if critical deviations were found, False otherwise
    """
    critical_count = len(stats['investigate'])
    
    if critical_count == 0:
        return False
        
    # Sort critical cases by severity (absolute difference)
    critical_cases = sorted(stats['investigate'], 
                          key=lambda x: x['abs_diff'], reverse=True)
    
    warning_msg = (f"WARNING: Found {critical_count} critical pressure difference deviations! "
                  f"This may indicate faulty network assignments or modeling errors.")
    
    if logger:
        logger.warning(warning_msg)
        logger.warning("Most severe cases:")
        for case in critical_cases[:3]:  # Show top 3
            logger.warning(f"  Edge {case['edge']} at {case['timestamp']}: "
                         f"{case['abs_diff']:.2f} Pa deviation ({case['rel_error']*100:.1f}%)")
    else:
        print(f" {warning_msg}")
        print("Most severe cases:")
        for case in critical_cases[:3]:
            print(f"  • Edge {case['edge']} at {case['timestamp']}: "
                  f"{case['abs_diff']:.2f} Pa deviation ({case['rel_error']*100:.1f}%)")
    
    return True

## Final pipeline function


def assign_data_pipeline(
    graph: ug.UESGraph,
    simulation_data_path: Union[str, Path], 
    start_date: datetime,
    end_date: datetime,
    time_interval: str,
    MASK: Optional[Dict[str, str]] = None,
    aixlib_version: str = "2.1.0",
    system_model_path: Optional[Union[str, Path]] = None,
    node_to_port_mapping: Optional[Dict] = None,
    logger: Optional[logging.Logger] = None
) -> ug.UESGraph:
    """
    Assign simulation data to a UESGraph network.
    
    This function processes simulation results and assigns time series data
    to network components (nodes and edges). It supports two modes:
    
    1. **Full assignment** (with node data): Requires either `node_to_port_mapping`
       or `system_model_path` to map simulation variables to graph nodes
    2. **Edge-only assignment**: When no mapping is available, only assigns
       data to edges (mass flows, pressure drops)
    
    Args:
        graph: UESGraph instance to assign data to
        simulation_data_path: Path to simulation results (.mat or .parquet)
        start_date: Start date for data processing
        end_date: End date for data processing  
        time_interval: Time interval for resampling (e.g., "15min", "1H")
                      No default - user must specify explicitly
        MASK: Custom variable name masks. If None, uses AixLib standard masks
        aixlib_version: AixLib version for standard masks (default: "2.1.0")
        system_model_path: Path to system model JSON (for creating port mapping)
        node_to_port_mapping: Pre-computed mapping from nodes to simulation ports
        logger: Logger instance. If None, creates a new file logger
        
    Returns:
        UESGraph instance with assigned simulation data
        
    Raises:
        FileNotFoundError: If simulation_data_path doesn't exist
        ValueError: If graph has no name set or data validation fails
        KeyError: If required simulation variables are missing
        
    Notes:
        - Either `node_to_port_mapping` OR `system_model_path` is required 
          for full data assignment including nodes
        - If both are None, only edge data (mass flows) will be assigned
        - Graph must have a name set in graph.graph["name"]
        
    Example:
        >>> import uesgraphs as ug
        >>> from datetime import datetime
        >>> 
        >>> # Load your network
        >>> graph = ug.UESGraph()  
        >>> graph.from_json("network.json", network_type="heating")
        >>> graph.graph["name"] = "my_network"
        >>> 
        >>> # Assign simulation data
        >>> graph_with_data = assign_data_pipeline(
        ...     graph=graph,
        ...     simulation_data_path="results.mat",
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 7), 
        ...     time_interval="15min",
        ...     system_model_path="system_model.json"
        ... )
        >>> 
        >>> # With custom masks
        >>> custom_masks = {
        ...     "m_flow": "custom.pipe{pipe_code}.flow",
        ...     "p_a": "custom.pipe{pipe_code}.pressure_in", 
        ...     "p_b": "custom.pipe{pipe_code}.pressure_out"
        ... }
        >>> graph_with_data = assign_data_pipeline(
        ...     graph=graph,
        ...     simulation_data_path="results.mat", 
        ...     start_date=datetime(2024, 1, 1),
        ...     end_date=datetime(2024, 1, 7),
        ...     time_interval="1H",
        ...     MASK=custom_masks
        ... )
    """
    # Set up logging
    if logger is None:
        logger = set_up_file_logger("assign_data_pipeline", level=logging.INFO)
    
    # Convert simulation_data_path to Path object  
    simulation_data_path = Path(simulation_data_path)
    
    # Validate graph has a name
    network_name = graph.graph.get("name")
    if not network_name:
        raise ValueError("Graph must have a name set in graph.graph['name']")
    
    # Check supply type from graph
    supply_type = graph.graph.get("supply_type", "supply")
    supply_type_prefix = {"supply": "", "return": "R"}
    
    logger.info("="*70)
    logger.info("STARTING DATA ASSIGNMENT PIPELINE")
    logger.info("="*70)
    logger.info(f"Network: {network_name}")
    logger.info(f"Graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    logger.info(f"Simulation data: {simulation_data_path}")
    logger.info(f"Time period: {start_date} to {end_date}")
    logger.info(f"Time interval: {time_interval}")
    logger.info(f"Supply type: {supply_type}")
    
    # Determine assignment mode based on available mapping options
    assignment_mode = _determine_assignment_mode(
        system_model_path, node_to_port_mapping, logger
    )
    
    try:
        # Step 1: Determine variable masks
        logger.info("Step 1/6: Setting up variable masks")
        if MASK is None:
            MASK = AIXLIB_MASKS[aixlib_version]
            logger.info(f"✓ Using AixLib {aixlib_version} standard masks")
        else:
            logger.info("✓ Using custom variable masks")
        
        # Step 2: Create or use port mapping (if available)
        port_mapping = None
        if assignment_mode == "full":
            logger.info("Step 2/6: Setting up port mapping for node assignment")
            
            if node_to_port_mapping is not None:
                port_mapping = node_to_port_mapping
                logger.info("✓ Using provided node-to-port mapping")
                
            elif system_model_path is not None:
                system_model_path = Path(system_model_path)
                if not system_model_path.exists():
                    raise FileNotFoundError(f"System model file not found: {system_model_path}")
                
                sysm_graph = ut.load_system_model_from_json(str(system_model_path))
                port_mapping = graph_transformation.map_system_model_to_uesgraph(sysm_graph, graph)
                logger.info(f"✓ Created port mapping from system model ({len(port_mapping)} components)")
                
        elif assignment_mode == "edges_only":
            logger.info("Step 2/6: Skipping port mapping - edge-only assignment mode")
            logger.warning("⚠️  No node data will be assigned (temperatures, pressures)")
        
        # Step 3: Process simulation data
        logger.info("Step 3/6: Processing simulation data")
        
        # Validate simulation data file exists
        if not simulation_data_path.exists():
            raise FileNotFoundError(f"Simulation data file not found: {simulation_data_path}")
        
        # Build filter list for required variables
        filter_list = build_filter_list_pipe(graph, mask=MASK, logger=logger)
        logger.info(f"✓ Built filter list with {len(filter_list)} variables")
        
        # Validate that all required columns exist
        column_validation = validate_columns_exist(
            file_path=str(simulation_data_path), 
            required_columns=filter_list,
            logger=logger
        )
        if not column_validation:
            raise KeyError("Required simulation variables not found in data file")
        
        # Load and process simulation results
        df = process_simulation_result(
            file_path=str(simulation_data_path), 
            filter_list=filter_list, 
            logger=logger
        )
        logger.info(f"✓ Loaded simulation data: {df.shape[0]} timesteps")
        
        # Step 4: Prepare DataFrame
        logger.info("Step 4/6: Preparing time series data")
        df = prepare_DataFrame(
            df, 
            start_date=start_date, 
            end_date=end_date,
            time_interval=time_interval, 
            logger=logger
        )
        logger.info(f"✓ Prepared DataFrame: {df.shape[0]} timesteps after filtering")
        
        # Step 5: Assign data to graph components
        logger.info("Step 5/6: Assigning data to graph components")
        
        if assignment_mode == "full":
            # Assign values to nodes (temperature and pressure)
            assign_node_values(graph, df, port_mapping, MASK, logger=logger)
            logger.info(f"✓ Assigned node data (temperature, pressure) to {len(graph.nodes)} nodes")
        
        # Assign values to edges (mass flow, pressure drop) - always done
        assign_edge_data(graph, MASK, df)
        logger.info(f"✓ Assigned edge data (mass flow, pressure drop) to {len(graph.edges)} edges")
        
        # Step 6: Validate results
        logger.info("Step 6/6: Validating assignment results")
        
        validate_edge_attributes(graph, MASK["edge"], df, logger=logger)
        logger.info("✓ Edge validation completed successfully")

        if assignment_mode == "full":
            validate_node_attributes(graph,MASK["node"],df, logger=logger)

            ## Additional test to asses node assignment based on pressures
            stats = assess_dp_quality(graph) 
            has_critical = _check_dp_quality_warnings(stats, logger)
            if has_critical:
                logger.warning("⚠️  Critical pressure difference deviations found!")
            else:
                logger.info("✓ Full validation completed successfully")

        
        logger.info("="*70)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(f"✓ Network '{network_name}' ready for analysis")
        logger.info(f"✓ Data period: {df.index.min()} to {df.index.max()}")
        logger.info(f"✓ Time resolution: {time_interval}")
        logger.info(f"✓ Assignment mode: {assignment_mode}")
        logger.info("="*70)
        
        return graph
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        logger.error("="*70)
        raise


def _determine_assignment_mode(
    system_model_path: Optional[Union[str, Path]], 
    node_to_port_mapping: Optional[Dict],
    logger: logging.Logger
) -> str:
    """
    Determine the assignment mode based on available mapping options.
    
    Returns:
        "full": Full assignment including nodes (requires mapping)
        "edges_only": Only edge assignment (no node data)
    """
    if node_to_port_mapping is not None:
        logger.info("Port mapping provided → Full assignment mode")
        return "full"
    elif system_model_path is not None:
        logger.info("System model provided → Full assignment mode")  
        return "full"
    else:
        logger.warning("No port mapping or system model → Edge-only assignment mode")
        logger.warning("Node temperatures and pressures will NOT be assigned")
        return "edges_only"


##### Helper functions

def get_supply_type_prefix(graph):
    supply_type = graph.graph.get("supply_type", "supply")
    supply_type_prefix = {"supply": "", "return": "R"}
    return supply_type_prefix.get(supply_type, "")

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

def list_supported_versions():
    """List all supported AixLib versions."""
    return list(AIXLIB_MASKS.keys())