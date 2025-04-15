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

from uesgraphs.data.mat_handler import mat_to_parquet

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

#### Functions 2: Data Processing ####

def process_parquet_file(file_path: str, filter_list: List[str], 
                        chunk_size: int = 100000) -> Generator[pd.DataFrame, None, None]:
    """
    Process a parquet file in chunks to reduce memory usage.
    
    Args:
        file_path: Path to the parquet file
        filter_list: List of column patterns to filter
        chunk_size: Number of rows to process at once
    """
    # Read parquet file metadata to get columns
    parquet_file = pq.ParquetFile(file_path)
    all_columns = parquet_file.schema.names
    
    # Pre-filter columns based on filter_list to reduce memory usage
    columns_to_read = []
    for pattern in filter_list:
        if pattern.endswith('$'):
            # Regex filter
            regex_pattern = pattern[:-1] + '$'
            columns_to_read.extend(
                col for col in all_columns 
                if re.match(regex_pattern, col)
            )
        else:
            # Simple string filter
            columns_to_read.extend(
                col for col in all_columns 
                if pattern in col
            )
    
    # Remove duplicates while preserving order
    columns_to_read = list(dict.fromkeys(columns_to_read))
    
    # Read and process the file in chunks
    for chunk in parquet_file.iter_batches(batch_size=chunk_size, columns=columns_to_read):
        yield chunk.to_pandas()

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

#### Functions 3: Data Processing ####

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
            graph.edges[edge]["press_drop"] = abs(graph.nodes[edge[0]]["press_flow"] - graph.nodes[edge[1]]["press_flow"])
            graph.edges[edge]["press_drop_length"] = graph.edges[edge]["press_drop"] / graph.edges[edge]["length"]
            
            graph.edges[edge]["temp_diff"] = abs(graph.nodes[edge[0]]["temperature_supply"] - graph.nodes[edge[1]]["temperature_supply"])
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

def plot_network(graph):
    vis = ug.Visuals(graph)
    fig = vis.show_network(show_plot=show_plot)