"""
UESGraphs Analysis Module
========================

Enhanced analysis capabilities for district heating networks.

This module provides tools for:
- Processing simulation data from Dymola/Modelica
- Assigning time series data to network components  
- Hydraulic and thermal analysis
- Performance calculations and visualizations

Main Functions:
--------------
- assign_simulation_data(): Main API for data assignment
- process_simulation_result(): Process parquet/mat files
- prepare_DataFrame(): Add datetime index and filtering

Example Usage:
-------------
```python
import uesgraphs as ug
from uesgraphs.analysis import assign_simulation_data, process_simulation_result

# Load network
graph = ug.UESGraph()
graph.from_json("network.json", network_type="heating")

# Process simulation data
graph_with_data = assign_simulation_data(
    graph, 
    "simulation_results.mat",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 7)
)
```
"""

# Import main functions from data_handling
from .data_handling.data_handling import (
    # File processing
    process_simulation_result,
    prepare_DataFrame,
    assign_data_pipeline,

    # Main API (TODO: implement)
    # assign_simulation_data,
    
    # Logger setup
    set_up_terminal_logger,
    set_up_file_logger,
)

# Version info
__version__ = "0.1.0"
__author__ = "Leon Kopka (leon.kopka@rwth-aachen.de)"

# Define public API
__all__ = [
    # Main API
    # "assign_simulation_data",  # TODO: uncomment when implemented
    
    # Core functions
    "process_simulation_result",
    "prepare_DataFrame",
    "assign_data_pipeline"
    # Utilities
    "set_up_terminal_logger", 
    "set_up_file_logger",
]