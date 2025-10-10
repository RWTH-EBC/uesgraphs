"""Utilies: Collection of all utility functions that are useful in several classes."""

import os
import logging
import tempfile
from datetime import datetime
from typing import Optional


def default_json_path():
    """
    Creates default output file UESgraphOutput in the user dictionary.

    Paramters
    ---------
    UESgraph_defaul_path : str
        Path, where uesgraph files will be saved.

    Returns
    -------
    path : str
        Path, where to save uesgraph files
    """

    UESgraph_default_path = os.path.expanduser("~")
    UESgraph_default_path = os.path.join(UESgraph_default_path, "UESgraphOutput")
    UESgraph_default_path = os.path.abspath(UESgraph_default_path)

    if not os.path.exists(UESgraph_default_path):
        os.mkdir(UESgraph_default_path)

    if os.path.isdir(UESgraph_default_path):
        os.chdir(UESgraph_default_path)

    path = UESgraph_default_path

    return path


def make_workspace(name_workspace=None):
    """Creates a local workspace with given name

    If no name is given, the general workspace directory will be used

    Parameters
    ----------
    name_workspace : str
        Name of the local workspace to be created

    Returns
    -------
    workspace : str
        Full path to the new workspace
    """

    this_dir = default_json_path()

    if not name_workspace:
        workspace = os.path.join(this_dir, 'Project')
    else:
        workspace = os.path.join(this_dir, name_workspace)

    if not os.path.exists(workspace):
        os.mkdir(workspace)

    return workspace


def name_uesgraph(name_workspace=None):
    """Gives the uesgraph a name

    Parameters
    ----------
    name_workspace : str
        Name of the workspace of the current uesgraph

    Returns
    -------
    name_uesgraph : str
        Name of the uesgraph according to its workspace
    """

    name_uesgraph = make_workspace.name_workspace

    return name_uesgraph


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


def get_attribute_case_insensitive(row, attribute_name):
    """
    Retrieve an attribute value from a dictionary, handling case insensitivity.
    
    This function tries to access the attribute with the original name first,
    then attempts to access it with different capitalizations if the original
    attempt fails.
    
    Parameters:
        row (dict): The dictionary containing the data
        attribute_name (str): The base name of the attribute to retrieve
    
    Returns:
        The value associated with the attribute, or None if not found
    """
    # Try the original attribute name first
    if attribute_name in row:
        return row[attribute_name]
    
    # Try lowercase and uppercase variations
    variations = [
        attribute_name.lower(),
        attribute_name.upper(),
        attribute_name.capitalize(),
        attribute_name.title()
    ]
    
    # Check each variation
    for variant in variations:
        if variant in row:
            return row[variant]
    
    # Return None if no matching attribute is found
    return None
