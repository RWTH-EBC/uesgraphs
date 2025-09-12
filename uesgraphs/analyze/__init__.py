"""
UESGraphs Analysis Module
========================

Enhanced analysis capabilities for district heating networks.

Main Functions:
- assign_data_pipeline(): Full pipeline for simulation data assignment
- process_simulation_result(): Process .mat/.parquet files
- prepare_DataFrame(): Add datetime indexing and filtering

Quick Start:
```python
from uesgraphs.analysis import assign_data_pipeline
from datetime import datetime

# Assign simulation data to network
graph_with_data = assign_data_pipeline(
    graph=graph,
    simulation_data_path="results.mat",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 7),
    time_interval="15min",
    system_model_path="system_model.json"
)
```
"""

# Main pipeline function
from .data_handling.data_handling import (
    assign_data_pipeline,
    process_simulation_result,
    prepare_DataFrame,
    set_up_terminal_logger,
    set_up_file_logger,
)

# MAT file handling
from .data_handling.mat_handler import (
    loadsim,
    mat_to_pandas,
    mat_to_parquet,
)

# System model mapping
from .data_handling.graph_transformation import (
    map_system_model_to_uesgraph,
)

# Version info
__version__ = "0.2.0"
__author__ = "Leon Kopka (leon.kopka@rwth-aachen.de)"

# Public API - main functions users need
__all__ = [
    "assign_data_pipeline",
    "process_simulation_result", 
    "prepare_DataFrame",
    "loadsim",
    "mat_to_pandas",
    "mat_to_parquet",
    "map_system_model_to_uesgraph",
    "set_up_terminal_logger",
    "set_up_file_logger",
]