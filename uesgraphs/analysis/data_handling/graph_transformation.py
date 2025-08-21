import itertools

def get_pipes_for_node(graph_sysm, node_id):
    """
    Identifies all pipes in the system model graph connected to a specified node in the
    uesgraphs
    Args:
        graph_sysm (uesgraphs.systemmodels.systemmodelheating.SystemModelHeating): 
                                The system model graph where pipes are nodes and 
                                     connections are edges
        node_id (str): The ID or name of the node for which to find connected pipes
    
    """
    relevant_pipes = []
    for pipe in graph_sysm.nodelist_pipe:
        if graph_sysm.nodes[pipe].get("node_0") == node_id or graph_sysm.nodes[pipe].get("node_1") == node_id:
            relevant_pipes.append(pipe)
    return relevant_pipes

def get_ports_for_network_node(graph_sysm, pipe_nodes_sysm):
    """
    Identifies all unique connection ports for a set of pipes that form a node in the UES graph.

    This function addresses the mapping between two different graph representations:
    1. System model graph (graph_sysm): Pipes are modeled as nodes, and connections between
       pipes are modeled as edges with port information.
    2. UES graph: Pipes are modeled as edges, and connections between pipes are modeled as nodes.

    In the system model, state changes occur within pipes (nodes), while connections maintain
    constant states. These connections correspond to nodes in the UES graph. This function
    finds all connections between the provided pipes, which represent a single node in the 
    UES graph.

    Args:
        graph_sysm (uesgraphs.systemmodels.systemmodelheating.SystemModelHeating): 
                                The system model graph where pipes are nodes and 
                                     connections are edges
        pipe_nodes_sysm (list): List of pipe IDs that are connected to the same node in 
                               the UES graph

    Returns:
        set: All unique port identifiers where these pipes connect, representing points 
             with identical states in the physical model
    """
    # Collect all unique ports connected to this node (set avoids duplicates)
    ports_per_node = set()

    # Check all possible pipe combinations (unordered pairs)
    for edge1, edge2 in itertools.combinations(pipe_nodes_sysm, 2):
        # If these pipes are connected in the system model
        if graph_sysm.has_edge(edge1, edge2):
            # Add the connection ports to our collection
            # These ports represent points with identical state in the model
            ports_per_node.add(graph_sysm.edges[edge1, edge2]['con1'])
            ports_per_node.add(graph_sysm.edges[edge1, edge2]['con2'])
            
    return ports_per_node

def get_ports_for_bldg_node(graph_sysm,name):
    """
    Identifies the connection ports for a building node (consumer or supplier).
    
    Building nodes are special terminal nodes that have only one pipe connection.
    Their port handling differs from junction nodes.

    Args:
        graph_sysm (uesgraphs.systemmodels.systemmodelheating.SystemModelHeating): 
                                The system model graph where pipes are nodes and 
                                     connections are edges
        name: str: The name of the building node for which to find connected ports
    Returns:
        set: A set of ports connected to the building node
    """
    for bldg_model in graph_sysm.nodelist_building:
        ports_per_bldg = set()
        # Find the building node in system model graph that matches the uesgraph node
        if name == graph_sysm.nodes[bldg_model]["name"]:
            # Get the edges connected to the building node
            adj_edges = graph_sysm.edges(bldg_model)
            if len(adj_edges) > 1:
                print(f"Interesting case, cause multiple pipes are connected to building {name}")
            # Since edges in the system models graph correspond to nodes in uesgraph both connections 
                # should get the same simulation results
            for edge in adj_edges:
                ports_per_bldg.add(graph_sysm.edges[edge]['con1'])
                ports_per_bldg.add(graph_sysm.edges[edge]['con2'])
            return ports_per_bldg
        
def validate_structural_node_port_mapping(uesgraph, node_to_ports_mapping):
   """
   Validates the structural integrity of the node-to-ports mapping.
   
   This function performs a structural validation only, checking that:
   1. All nodes in the UES graph have a corresponding entry in the mapping
   2. Every node has at least two ports assigned (the minimum required for any connection)
   
   Note: This is only a structural validation and does not verify the actual values
   or physical correctness of the ports. A complete validation would require comparing
   actual port values against expected physical constraints.
   
   Args:
       uesgraph (uesraphs object): The UES graph containing all nodes to validate
       node_to_ports_mapping (dict): The mapping from node IDs to port lists
       
   Raises:
       ValueError: If any structural validation criteria are not met, with specific
                  details about which nodes failed validation and why
   """
   # Check 1: All nodes from the UES graph must be present in the mapping
   missing_nodes = set(uesgraph.nodes) - set(node_to_ports_mapping.keys())
   if missing_nodes:
       raise ValueError(f"Missing port mappings for nodes: {missing_nodes}")
   
   # Check 2: All nodes should have at least two ports (minimum requirement for connections)
   invalid_nodes = []
   for node, ports in node_to_ports_mapping.items():
       # Every connection needs at least two ports
       if len(ports) < 2:
           invalid_nodes.append(f"Node {node} has only {len(ports)} ports, minimum required is 2")
   
   if invalid_nodes:
       raise ValueError("Structural validation failed:\n" + "\n".join(invalid_nodes))
   
def map_system_model_to_uesgraph(graph_sysm,uesgraph):
    """
    Maps each node in the UES graph to its corresponding ports in the system model graph.
    
    This function handles the transformation between two different graph representations:
    1. UES graph: Models the physical network where pipes are edges and junctions are nodes
    2. System model graph: Models the simulation components where pipes are nodes and
       connections between pipes are edges    


    Args:
        graph_sysm (uesgraphs.systemmodels.systemmodelheating.SystemModelHeating): 
                                The system model graph where pipes are nodes and 
                                     connections are edges
        uesgraph (uesgraphs.uesgraph.UESGraph): The UES graph where pipes are edges and 
                                                connections are nodes
    
    Returns:
        dict: Mapping from UES graph node IDs to lists of corresponding system model ports
        
    Raises:
        ValueError: If a non-building node has only one pipe connection (open end)
    """
    node_to_ports_mapping = {}
    
    # Iterate over all nodes in the UES graph
    for node in uesgraph.nodes:
        name = uesgraph.nodes[node]["name"]
        # Get all pipes connected to this node in the system model
        relevant_pipes = get_pipes_for_node(graph_sysm, name)
        #print(f"For node {node} found {relevant_pipes} pipes")
        
        # Handle based on the number of connected pipes
        if len(relevant_pipes) == 1:
            # Terminal nodes should only be buildings (consumers or suppliers)
            if uesgraph.nodes[node]["node_type"] == "building":    
                node_to_ports_mapping[node] = list(get_ports_for_bldg_node(graph_sysm, name))
            else:
                raise ValueError(f"Node {node} has an open end, meaning just one pipe is connected to it, while its not a consumer or supplier")
        else:
            # For junction nodes, find all unique ports connected to the pipes
            node_to_ports_mapping[node]= list(get_ports_for_network_node(graph_sysm, relevant_pipes))

    #Validate the mapping structure
    validate_structural_node_port_mapping(uesgraph, node_to_ports_mapping)
    
    return node_to_ports_mapping


