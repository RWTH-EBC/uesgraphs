
import re
from typing import List, Dict, Generator, Optional, Union, Tuple
import os

import logging
import tempfile
from datetime import datetime


#### Global Variables ####
MASKS = None  # Dictionary to store masks for column names


#### Logging Setup ####
def set_up_logger(name: str, log_dir: Optional[str] = None, level: int = logging.ERROR) -> logging.Logger:
    """
    Set up a logger with file output for data handling operations.
    
    Args:
        name: Logger name
        log_dir: Directory for log files (default: temp directory)
        level: Logging level (default: ERROR)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if log_dir is None:
        log_dir = tempfile.gettempdir()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    print(f"Logfile findable here: {log_file}")
    
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def check_input_file(file_path):
    if not file_path:
        raise ValueError("File path cannot be empty")

    base_path = os.path.splitext(file_path)[0]
    gzip_path = f"{base_path}.gzip"

    # Check for gzip first
    if os.path.exists(gzip_path):
        return gzip_path
    # Then check for .mat
    mat_path = f"{base_path}.mat"
    if os.path.exists(mat_path):
        try:
            print(f"Converting .mat file to parquet: {mat_path}")
            gzip_new = mat_to_parquet(save_as = base_path, fname = mat_path,with_unit=False)
            print(f"Converted .mat file to parquet: {gzip_new}")
            return gzip_new
        except:
            raise ValueError(f"Could not convert .mat file to parquet: {mat_path}") 
    # Finally check if file exists with any extension
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    
def check_input_file(file_path: str) -> str:
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
    logger = get_module_logger()
    
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

