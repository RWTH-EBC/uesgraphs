import uesgraphs as ug


import os

from typing import List, Dict, Generator, Optional
import pyarrow.parquet as pq
import re
import pandas as pd

import logging

from datetime import datetime
import tempfile

import numpy as np
import sys

import networkx as nx

from uesgraphs.data.mat_handler import mat_to_parquet



import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import FuncFormatter

#### Global Variables ####

MASKS = None # Dictionary to store masks for column names

#### Functions 1: Logger ####
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


def process_simulation_result(file_path: str, filter_list: List[str]) -> pd.DataFrame:
    """
    Process a single simulation result file and return the processed DataFrame.
    
    Args:
        file_path: Complete path to the simulation result file
        filter_list: List of column patterns to filter
        
    Returns:
        pd.DataFrame: Processed and filtered DataFrame from the simulation results
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If the file path is empty or invalid
    """
    file_path = check_input_file(file_path=file_path)
    print(f"Processing: {file_path}")
    
    # Initialize an empty list for filtered chunks
    filtered_chunks = []
    
    # Process the file in chunks
    for chunk in process_parquet_file(file_path, filter_list):
        filtered_chunks.append(chunk)
    
    # Combine all chunks into a single DataFrame
    if not filtered_chunks:
        return pd.DataFrame()  # Return empty DataFrame if no data was processed
        
    result_df = pd.concat(filtered_chunks, axis=0)
    
    # Clear the chunks list to free memory
    filtered_chunks.clear()
    
    return result_df


def prepare_DataFrame(df, base_date=datetime(2024, 1,1),time_interval="15min",start_date=None,end_date=None):
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
    
    Returns:
   
    DataFrame: A DataFrame containing the data from the parquet file for the specified time period.
    """
    try:
        # Create datetime index with specified frequency    
        datetime_index = pd.date_range(start=base_date, periods=len(df), freq=time_interval)
        
        # Set the index of the DataFrame to the datetime index
        df.index = datetime_index

        #Filter by data_range if specified
        if start_date is not None and end_date is not None:
            return df.loc[start_date:end_date]
        elif start_date is not None:
            return df.loc[start_date:]
        elif end_date is not None:
            return df.loc[:end_date]
        # Benenne den Index um
        df.index.name = 'DateTime'

        return df
    except ValueError as e:
        raise ValueError(f"Error create data range with frequency {time_interval} and base date {base_date}."
                         f"Original error: {e}") 


def get_mostfrequent_value(liste):
    #Find unique values and frequencies
    unique_values, counts = np.unique(liste, return_counts=True)
    #Find index of most frequent value and save that value
    max_index = np.argmax(counts)
    result = float(unique_values[max_index])
    return result

def get_peripheral_value(node, edge, heating_network, param, value_a, value_b):
    for node2 in edge:
        if node2 != node:
            value_assigned_node = heating_network.nodes[node2][param]
            if abs(value_a - value_assigned_node) < abs(value_b - value_assigned_node):
                result = value_b
            else:
                result = value_a
    return result

def get_node_values(heating_network, row,pipe_type=""):
    nodes = sorted(heating_network.nodes)
    assigned_nodes = []
    nodes_peripheral = []
    #Neighbor-algorihm: find the most frequent value at a node where at least 2 edges meet
    for node in nodes:         
        edges =  heating_network.edges(node) #Find adjacent edges
        #If we find only one edge we are regarding a peripheral node, which cant be solved by the neigbor algorithm
        if len(edges)> 1:
            pressures = []
            temperatures=[]

            for edge in edges:
                pipe_name= heating_network.edges[edge]['name']
                pressure_a = row[MASKS["p_a"].format(pipe_code=pipe_name, type=pipe_type)]
                pressure_b = row[MASKS["p_b"].format(pipe_code=pipe_name, type=pipe_type)]

                temperature_a = row[MASKS["T_a"].format(pipe_code=pipe_name, type=pipe_type)]
                temperature_b = row[MASKS["T_b"].format(pipe_code=pipe_name, type=pipe_type)]

                pressures.extend([pressure_a, pressure_b])
                temperatures.extend([temperature_a,temperature_b])
            pressure = get_mostfrequent_value(pressures)
            temperature = get_mostfrequent_value(temperatures)
            if pressure_a == pressure:
                heating_network.nodes[node]["press_name"] = MASKS["p_a"].format(pipe_code=pipe_name, type=pipe_type)
            elif pressure_b == pressure:
                heating_network.nodes[node]["press_name"] = MASKS["p_b"].format(pipe_code=pipe_name, type=pipe_type)
            heating_network.nodes[node]["press_flow"] = pressure

            if temperature_a == temperature:
                heating_network.nodes[node]["temp_name"] = MASKS["T_a"].format(pipe_code=pipe_name, type=pipe_type)
            elif temperature_b == temperature:
                heating_network.nodes[node]["temp_name"] = MASKS["T_b"].format(pipe_code=pipe_name, type=pipe_type)
            heating_network.nodes[node]["temperature_supply"] = temperature
            assigned_nodes.append(node)
        else:
            nodes_peripheral.append(node)
    #Peripheral-algorithm: Takes the not solved nodes from the neighbor-algorithm. Since we're still not sure
            # if the port_a or ports_b value is the right one, we compare the simulation results with the already assigned node
            # that was solved by the neighbor-algorithm.
    for node in nodes_peripheral:
        edge = list(heating_network.edges(node))[0]
        pipe_name = heating_network.edges[edge]["name"]
        pressure_a = row[MASKS["p_a"].format(pipe_code=pipe_name, type=pipe_type)]
        pressure_b = row[MASKS["p_b"].format(pipe_code=pipe_name, type=pipe_type)]

        temperature_a = row[MASKS["T_a"].format(pipe_code=pipe_name, type=pipe_type)]
        temperature_b = row[MASKS["T_b"].format(pipe_code=pipe_name, type=pipe_type)]
        
        pressure = get_peripheral_value(node, edge, heating_network, "press_flow", pressure_a, pressure_b)
        if pressure_a == pressure:
            heating_network.nodes[node]["press_name"] = MASKS["p_a"].format(pipe_code=pipe_name, type=pipe_type)
        elif pressure_b == pressure:
            heating_network.nodes[node]["press_name"] = MASKS["p_b"].format(pipe_code=pipe_name, type=pipe_type)
        heating_network.nodes[node]["press_flow"] = pressure

        temperature = get_peripheral_value(node, edge, heating_network, "temperature_supply", temperature_a, temperature_b)
        if temperature_a == temperature:
            heating_network.nodes[node]["temp_name"] = MASKS["T_a"].format(pipe_code=pipe_name, type=pipe_type)
        elif temperature_b == temperature:
            heating_network.nodes[node]["temp_name"] = MASKS["T_b"].format(pipe_code=pipe_name, type=pipe_type)
        heating_network.nodes[node]["temperature_supply"] = temperature
        
        assigned_nodes.append(node)
    
    ####Assert
    if len(assigned_nodes) == len(nodes):
        print("Assignment of pressure to nodes completed")
    else:
        print(f"Assignmnet failed -- severe {len(assigned_nodes)} und {len(nodes)}")
    return heating_network

def check_supply_type(graph):
    # Check if the graph is a supply or return graph
    if "supply_type" not in graph.graph:
        raise ValueError("The graph does not have a supply_type attribute")
    if graph.graph["supply_type"] not in ["supply", "return"]:
        raise ValueError("The graph supply_type attribute must be either 'supply' or 'return'")
    return graph.graph["supply_type"]

def get_MASKS(aixlib_version):
    """Returns the correct variable masks for different AixLib versions.
    
    The naming convention for variables in the simulation model depends on the AixLib version
    used to build it. The key difference is in how ports are referenced:
    - Version 2.1.0: Uses direct port access (e.g., port_b.p)
    - Earlier versions: Uses array indexing for ports_b (e.g., ports_b[1].p)
    
    Args:
        aixlib_version: Version string of AixLib used to build the model
        
    Returns:
        Dictionary mapping variable types to their full path in the simulation model
        
    """
    if aixlib_version == "2.1.0":
        masks = {"m_flow": "networkModel.pipe{pipe_code}{type}.port_a.m_flow",
         "dp": "networkModel.pipe{pipe_code}{type}.dp",
         "p_a": "networkModel.pipe{pipe_code}{type}.port_a.p",
         "p_b": "networkModel.pipe{pipe_code}{type}.port_b.p",
         "T_a": "networkModel.pipe{pipe_code}{type}.sta_a.T",
         "T_b": "networkModel.pipe{pipe_code}{type}.sta_b.T",
         }
    else:
        masks = {"m_flow": "networkModel.pipe{pipe_code}{type}.port_a.m_flow",
         "p_a": "networkModel.pipe{pipe_code}{type}.port_a.p",
         "p_b": "networkModel.pipe{pipe_code}{type}.ports_b[1].p",
         "T_a": "networkModel.pipe{pipe_code}{type}.sta_a.T",
         "T_b": "networkModel.pipe{pipe_code}{type}.sta_b[1].T",
         }
    return masks


#### Functions 4: Data Assignment (main) ####

def assign_data_to_uesgraphs(graph,sim_data,start_date,end_date, aixlib_version ="2.1.0",time_interval="15min"):
    
    check_supply_type(graph) # Check if the graph is a supply or return graph

    supply_type_prefix = {"supply": "", "return": "R"}

    global MASKS
    MASKS = get_MASKS(aixlib_version)
    try:

        filter_list = []
        for edge in graph.edges:
            pipe_code = graph.edges[edge]["name"]
            for mask in MASKS:
                filter_list.append(MASKS[mask].format(pipe_code=pipe_code, 
                                                    type=supply_type_prefix[graph.graph["supply_type"]]))
        df = process_simulation_result(file_path=sim_data, filter_list=filter_list)
        df = prepare_DataFrame(df,start_date=start_date, end_date=end_date,time_interval=time_interval)
        
        graph = get_node_values(graph, df.iloc[0],pipe_type=supply_type_prefix[graph.graph["supply_type"]])
        
        for node in graph.nodes:
            graph.nodes[node]["press_flow"] = df[graph.nodes[node]["press_name"]]
            graph.nodes[node]["temperature_supply"] = df[graph.nodes[node]["temp_name"]]
        
        for edge in graph.edges:
            graph.edges[edge]["m_flow"] = df[MASKS["m_flow"].format(pipe_code=graph.edges[edge]["name"],
                                                                type=supply_type_prefix[graph.graph["supply_type"]])]
            #graph.edges[edge]["press_drop"] = abs(graph.nodes[edge[0]]["press_flow"] - graph.nodes[edge[1]]["press_flow"])
            #graph.edges[edge]["press_drop_length"] = graph.edges[edge]["press_drop"] / graph.edges[edge]["length"]
            dp = df[MASKS["dp"].format(pipe_code=graph.edges[edge]["name"],type=supply_type_prefix[graph.graph["supply_type"]])]
            graph.edges[edge]["press_drop"] = abs(dp)
            #graph.edges[edge]["temp_diff"] = abs(graph.nodes[edge[0]]["temperature_supply"] - graph.nodes[edge[1]]["temperature_supply"])
    except KeyError as e_key:
        if "ports_b[1]" in str(e_key):
            raise KeyError(f"Key: {e_key}  not found in data."
                  'Try using aixlib_version="2.1.0" when calling assign_data_to_uesgraphs'
                  "For more information see method get_MASKS(aixlib_version) in analyze.py"
            ) from e_key
        elif "port_b" in str(e_key):
            raise KeyError(f"Key: {e_key}  not found in data."
                           'Try using aixlib_version="2.0.0" when calling assign_data_to_uesgraphs'
                  " For more information see method get_MASKS(aixlib_version) in analyze.py"
            ) from e_key
        else:
            raise KeyError(f"Key: {e_key}  not found in data."
                  "Unknown Error. Check your data if it complies with mapping of get_MASKS(aixlib_version) in analyze.py"
            ) from e_key
    return graph


#### Functions 5: Data post-processing ####

## Functions 5.1: Pump Power Analysis

def pump_power_analysis(graph, plot=True, output_dir=None, config=None):
    """
    Perform a complete pump power and energy analysis for a district heating network.
    
    This function orchestrates the full pump analysis workflow by calculating the required 
    pump power, converting it to energy consumption over time, optionally plotting the 
    results, and saving the data to a file if specified.
    
    Parameters
    ----------
    graph : uesgraphs.UESGraph
        A graph representation of the heating network with hydraulic attributes.
    plot : bool, default=True
        Whether to generate visualizations of the pump energy consumption.
    output_dir : str or Path, optional
        Directory path where outputs (plots and CSV files) should be saved.
        If None, results are not saved to disk.
    config : dict, optional
        Configuration parameters for pump power calculations including efficiency factors
        and operational settings.
    
    Returns
    -------
    pandas.DataFrame
        DataFrame containing time series of pump energy consumption with timestamps as index.
    
    Notes
    -----
    - The function requires proper hydraulic attributes in the graph (pressure drops, flows)
    - The returned DataFrame includes columns for energy consumption in different units
    - When saving results, the function creates 'pump_energy.csv' in the output_dir
    - The plotting and saving operations are skipped if the respective parameters are not provided
    """
    # Step 1: Calculate pump power requirements
    graph, pump_power_df = calculate_central_pump_power(graph, config)
    
    # Step 2: Convert power to energy consumption over time
    pump_energy_df = calculate_pump_energy(pump_power_df)
    
    # Step 3: Generate visualizations if requested
    if plot:
        plot_pump_energy(pump_energy_df, output_dir)
    
    # Step 4: Save results to disk if output directory is specified
    if output_dir:
        pump_energy_df.to_csv(os.path.join(output_dir, "pump_energy.csv"), index=True)
    
    return pump_energy_df

def calculate_central_pump_power(graph, config=None):
    """
    Calculate pump power requirements for a district heating network.
    
    This function analyzes a heating network graph to determine the required pump power 
    based on hydraulic pressure drops, flow rates, and pump configuration parameters.
    It performs time series analysis for each timestamp in the network data.
    
    Parameters
    ----------
    graph : ug.UESGraph
        A graph representation of the heating network with hydraulic attributes.
        Must contain time series data for pressure drops and mass flow rates.
    config : dict, optional
        Configuration dictionary with the following keys:
        - eta_pump: float, pump efficiency factor (default: 0.8)
        - dp_pump: float, internal pump pressure drop in Pa (default: 1000)
        - density_func: callable or float, water density function or constant value
          If callable, must accept timestamp and temperature parameters
    
    Returns
    -------
    tuple
        A tuple containing:
        - The original graph with potentially modified attributes
        - pandas.DataFrame with time series of pump power calculations including:
          * timestamp: time index
          * source_node: ID of the supply node
          * max_pressure_node: node with maximum pressure drop
          * max_pressure_value: maximum pressure drop value in Pa
          * dp_tot: total pressure drop in Pa (including return pipe and pump)
          * volume_flow: volume flow rate in m³/s
          * pump_power: calculated pump power in kW
          * rho: water density in kg/m³
          * eta_pump: pump efficiency factor
          * dp_pump: internal pump pressure drop in Pa
          * pressure_*: accumulated pressure to each node
    
    Raises
    ------
    TypeError
        If the provided graph is not an instance of UESGraph
    
    Notes
    -----
    - Currently supports only one supply node in the network
    - Assumes symmetric pressure drops in supply and return pipes
    - Uses the formula: P = (dp_tot * V_dot) / (eta_pump * 1000)
    - Where dp_tot = 2 * max_pressure_value + dp_pump
    """
    if not isinstance(graph, ug.UESGraph):
        raise TypeError("graph must be an instance of UESGraph")
    
    # Default configuration parameters
    default_config = {
        "eta_pump": 0.8,                            # Default pump efficiency
        "dp_pump": 1000,                            # Default internal pump pressure drop [Pa]
        "density_func": lambda t, temp=None: 998    # Default density function for water at 20°C [kg/m³]
    }

    # Initialize configuration with defaults
    if config is None:
        config = {}

    # Merge provided configuration with defaults
    for key, value in default_config.items():
        if key not in config:
            config[key] = value

    # Store results in a list
    results = []

    # Start algorithm by finding supply nodes
    source_nodes, source_edges = find_source_nodes(graph)

    # Process each supply node in the network
    # Note: Currently only one supply node is fully supported
    for source_node in source_nodes:
        # Get time index from the pressure drop time series of the source edge
        time_index = graph.edges[source_edges[0]]["press_drop"].index
        
        # Analyze network at each time point
        for t in time_index:
            # Create a snapshot of the graph at the current time point
            graph_t = get_graph_at_time(graph, t)
            
            # Calculate accumulated pressure drops from source to all nodes
            max_pressure_node, max_pressure_value, acc_pressures = calculate_accumulated_pressure_drop(
                graph_t, source_node
            )
            
            # Calculate fluid density
            if callable(config["density_func"]):
                density = config["density_func"](t, temp=graph_t.nodes[source_node]["temperature_supply"])
            else:
                density = config["density_func"]
                
            # Calculate volume flow rate from mass flow [m³/s]
            source_edge = list(graph_t.edges(source_node))[0]
            volume_flow = abs(graph_t.edges[source_edge]["m_flow"]) / density
            
            # Calculate total pressure drop [Pa]
            dp_pump = config["dp_pump"]  # Internal pump pressure drop
            # Multiply by 2 to account for supply and return pipes
            dp_tot = max_pressure_value * 2 + dp_pump
            
            # Calculate pump power using the formula: P = (dp_tot * V_dot) / (eta_pump * 1000) [kW]
            eta_pump = config["eta_pump"]
            pump_power = (dp_tot * volume_flow) / (eta_pump * 1000)

            # Create result entry with all calculated values
            result_entry = {
                'timestamp': t,
                'source_node': source_node,
                'max_pressure_node': max_pressure_node,
                'max_pressure_value': max_pressure_value,
                'dp_tot': dp_tot,
                'volume_flow': volume_flow,
                'pump_power': pump_power,
                'rho': density,
                'eta_pump': eta_pump,
                'dp_pump': dp_pump,
            }
            
            # Add pressure values for each node
            for node, pressure in acc_pressures.items():
                result_entry[f'pressure_{node}'] = float(pressure)
                
            results.append(result_entry)
            
    # Create a DataFrame from the results
    pump_power_df = pd.DataFrame(results)
    
    return graph, pump_power_df

def find_source_nodes(graph):
    """
    Identifies source nodes and their connected edges in a heating network graph.
    
    Source nodes are defined as nodes with the attribute 'is_supply_heating' set to True.
    These typically represent heat generation facilities in district heating networks.
    
    Parameters
    ----------
    graph : networkx.Graph
        A graph representing a heating network with nodes potentially having
        the 'is_supply_heating' attribute.
    
    Returns
    -------
    tuple
        A tuple containing two lists:
        - source_nodes: List of node identifiers that are marked as supply/source nodes
        - source_edges: List of edges (tuples) connecting source nodes to the network
    
    Raises
    ------
    ValueError
        If no source edges are found in the graph, making pump power calculation impossible.
    
    Notes
    -----
    - Multiple source nodes are allowed but will trigger a warning message
    """
    source_nodes = []
    source_edges = []
    
    # Identify all nodes marked as heat supply sources
    for node in graph.nodes:
        if graph.nodes[node].get("is_supply_heating", False):
            source_nodes.append(node)
            
            # Get the edges connected to this source node
            node_edges = list(graph.edges(node))
            if node_edges:  # Check if the node has any connected edges
                source_edges.append(node_edges[0])
    
    # Validation and warning messages
    if len(source_nodes) > 1:
        print(f"More than one source node found in graph {graph.graph.get('name', 'unnamed')}.")
    
    if not source_nodes:
        error_msg = f"No source nodes found in graph {graph.graph.get('name', 'unnamed')}. Pump power calculation not possible."
        print(error_msg)
        raise ValueError(error_msg)
        
    return source_nodes, source_edges

def get_graph_at_time(graph, time_point):
    """
    Creates a snapshot of the graph at a specific time point.
    
    Extracts values from time series data (pandas Series) in both edge and node 
    attributes at the specified time point to create a static graph representation.
    
    Parameters
    ----------
    graph : networkx.Graph or uesgraphs.UESGraph
        The input graph containing time series data as pandas Series in its 
        node and edge attributes.
    time_point : datetime-like or hashable
        The time point at which to extract values from time series data.
        Must be a valid index for the pandas Series attributes.
    
    Returns
    -------
    uesgraph
        A new graph with the same structure as the input graph, but with 
        time series attributes replaced by their values at the specified time point.
    
    Notes
    -----
    - Time series data should be stored as pandas Series with a time index
    - Non-time series attributes remain unchanged
    - Raises KeyError if time_point is not in the index of any time series
    """
    snapshot = graph.copy()
    
    # Process edge attributes
    for u, v, data in snapshot.edges(data=True):
        for key in data:
            if isinstance(data[key], pd.Series):
                snapshot[u][v][key] = data[key].loc[time_point]
    
    # Process node attributes
    for node, data in snapshot.nodes(data=True):
        for key in data:
            if isinstance(data[key], pd.Series):
                snapshot.nodes[node][key] = data[key].loc[time_point]
                
    return snapshot

def calculate_accumulated_pressure_drop(graph, source_node, key="press_drop"):
    """
    Calculate the accumulated pressure drop from a source node to all other nodes in the network.
    
    This function uses Dijkstra's algorithm to determine the shortest path from the source node
    to all other nodes in the graph, where the path length is weighted by the pressure drop. 
    It returns the node with the maximum accumulated pressure drop, its value, and a dictionary 
    containing the accumulated pressure drop for all nodes.
    
    Parameters
    ----------
    graph : networkx.Graph or uesgraphs.UESGraph
        A graph representing a heating network with 'press_drop' attributes on edges.
    source_node : node
        The starting node (typically a heat source or plant) from which to calculate 
        accumulated pressure drops.
    key : str, optional
        The edge attribute name used to calculate the pressure drop. Default is 'press_drop'.
    
    Returns
    -------
    tuple
        A tuple containing three elements:
        - max_pressure_node : The node with the maximum accumulated pressure drop
        - max_pressure_value : float, the maximum accumulated pressure drop value
        - acc_pressures : dict, mapping each node to its accumulated pressure drop from source
    
    Notes
    -----
    - The edge attribute key (default: "press_drop") must exist for all edges in the network
    - This function is essential for identifying critical paths in the network
    - The maximum pressure drop node often represents the hydraulic critical consumer
    """
    # Calculate accumulated pressure drops to all nodes using Dijkstra's algorithm
    acc_pressures = nx.single_source_dijkstra_path_length(
        graph, source_node, weight=key
    )
    
    # Find the node with the maximum accumulated pressure drop
    max_pressure_node = max(acc_pressures, key=acc_pressures.get)
    
    # Get the maximum pressure drop value
    max_pressure_value = acc_pressures[max_pressure_node]
    
    return max_pressure_node, max_pressure_value, acc_pressures

def calculate_pump_energy(pump_power_df):
    """
    Calculate energy consumption from pump power time series data.
    
    This function calculates the energy consumption of pumps by integrating
    power values over time. It computes the time differences between consecutive 
    measurements, calculates energy consumption for each interval, and provides 
    cumulative energy values.
    
    Parameters
    ----------
    pump_power_df : pandas.DataFrame
        DataFrame containing pump power data with a 'timestamp' column in
        datetime format and a 'pump_power' column containing power values in kW.
    
    Returns
    -------
    pandas.DataFrame
        The input DataFrame with additional columns:
        - time_diff: timedelta between consecutive timestamps
        - time_diff_hours: time difference in hours
        - energy: energy consumed in each interval in kWh
        - cumulative_energy: running sum of energy consumption in kWh
    
    Notes
    -----
    - This function assumes that the power remains constant between timestamps
    - Timestamps must be sortable datetime objects
    - The first interval uses a time difference of 0, resulting in 0 energy
    - Energy calculation is based on the formula: Energy (kWh) = Power (kW) × Time (h)
    """
    # Sort by timestamp to ensure chronological order for accurate time differencing
    sorted_df = pump_power_df.sort_values('timestamp')
    
    # Calculate time differences between consecutive measurements
    sorted_df['time_diff'] = sorted_df['timestamp'].diff().fillna(pd.Timedelta(hours=0))
    
    # Convert time differences to hours for energy calculation (kW × h = kWh)
    sorted_df['time_diff_hours'] = sorted_df['time_diff'].dt.total_seconds() / 3600
    
    # Calculate energy consumption for each time interval (kWh)
    sorted_df['energy'] = sorted_df['pump_power'] * sorted_df['time_diff_hours']
    
    # Calculate running total of energy consumption
    sorted_df['cumulative_energy'] = sorted_df['energy'].cumsum()
    
    return sorted_df

def plot_pump_energy(df, output_dir=None, label=""):
    """
    Generate a visualization of cumulative pump energy consumption over time.
    
    Creates a time series plot of the cumulative energy consumption from the pump
    power analysis results, with adaptive time axis formatting based on the data range.
    
    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame containing pump energy data with at minimum the following columns:
        - timestamp: datetime or convertible to datetime
        - cumulative_energy: float, the cumulative energy consumption in kWh
    output_dir : str or Path, optional
        Directory where the plot should be saved. If None, the plot is not saved.
    label : str, default=""
        Label for the data series in the plot legend.
    
    Returns
    -------
    None
        The function displays the plot and optionally saves it to disk.
    
    Notes
    -----
    - The function automatically formats the time axis based on the data time range
    - The plot is saved as 'energy_consumption_plot.png' if output_dir is provided
    - The figure is displayed using plt.show() which may block execution in non-interactive environments
    """

    
    # Convert timestamp to datetime if it's not already
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Create figure with appropriate size for time series visualization
    plt.figure(figsize=(12, 6))
    
    # Plot the cumulative energy consumption
    plt.plot(df['timestamp'], df['cumulative_energy'], label=label, linewidth=2)
    
    # Determine appropriate date formatting based on the data time range
    time_range = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
    if time_range > 86400 * 30:  # More than 30 days
        date_format = '%Y-%m-%d'
        locator = mdates.WeekdayLocator(interval=1)  # Weekly ticks
    elif time_range > 86400 * 7:  # More than a week
        date_format = '%Y-%m-%d'
        locator = mdates.DayLocator(interval=2)  # Every other day
    else:
        date_format = '%m-%d %H:%M'
        locator = mdates.DayLocator(interval=1)  # Daily ticks
    
    # Apply date formatting to the x-axis
    ax = plt.gca()
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
    
    # Rotate date labels for better readability
    plt.xticks(rotation=45, ha='right')
    
    # Add grid for better data interpretation
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Ensure sufficient space for labels and other elements
    plt.tight_layout()
    
    # Configure y-axis formatter for consistent energy value representation
    from matplotlib.ticker import FuncFormatter
    def kwh_formatter(x, pos):
        return f'{x:.1f}'
    
    ax.yaxis.set_major_formatter(FuncFormatter(kwh_formatter))
    
    # Add titles and axis labels
    plt.title('Cumulative Energy Consumption Over Time', fontsize=14)
    plt.xlabel('Timestamp', fontsize=12)
    plt.ylabel('Cumulative Energy (kWh)', fontsize=12)
    
    # Show legend only if label is provided
    if label:
        plt.legend()
    
    # Save the plot if output directory is specified
    if output_dir:
        output_path = os.path.join(output_dir, 'energy_consumption_plot.png')
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Plot saved to {output_path}")
    
    # Display the plot
    plt.show()

def plot_network(graph):
    vis = ug.Visuals(graph)
    fig = vis.show_network(show_plot=show_plot)