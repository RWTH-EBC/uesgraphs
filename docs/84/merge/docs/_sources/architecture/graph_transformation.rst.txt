Graph Transformation
====================

Mapping between UES Graph and System Model representations.

Conceptual Overview
-------------------

This framework addresses the challenge of mapping between two different graph representations of the same energy distribution system.

Graph Representation Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+-------------------+------------------------+------------------------+
| Aspect            | UES Graph              | System Model Graph     |
|                   |                        | (Modelica)             |
+===================+========================+========================+
| **Nodes**         | Junctions/connection   | Pipes and components   |
|                   | points                 |                        |
+-------------------+------------------------+------------------------+
| **Edges**         | Physical pipes         | Connections between    |
|                   |                        | components             |
+-------------------+------------------------+------------------------+
| **State changes** | Constant at nodes      | Occur within pipes     |
|                   |                        | (nodes)                |
+-------------------+------------------------+------------------------+
| **Purpose**       | Network topology       | Simulation model       |
+-------------------+------------------------+------------------------+

Why This Transformation Matters
--------------------------------

The transformation is necessary because the uesgraphs gets transformed for simulation model generation ( link to model generation pipeline). In the uesgraphs an edge describes what in real life would be a pipe, it links nodes. The nodes can be a demand, supply or junction points of edges. In the systemmodelheating-graph, that is used as basis for the simulation model, the edges are translated into nodes. The underlying philosophy is that every node represents an object, which can be a demand, supply or pipe. The former junction points of the uesgraphs get translated into edges. They will only describe the connection of the different objects to each other. This transformation makes it not trivial to map simulation result data back onto the uesgraphs. The simulation contains for example a pipe with a port_a and port_b. The pipe is represented in our systemmodelheating-graph through a node. But in our uesgraphs it is an edge and the ports would be the nodes connected by the edge. Depending on the properties of interest, this becomes a tricky part. While extensove sizes are constant over an pipe e.g. mass flow, those can be easily mapped onto the according edge on the uesgraphs. But for intensive sizes e.g. temperature or pressure it matters if you regard the beginning or the end of the pipe (port_a or port_b). At the same time intensive sizes are "constant" in a node. The mapping process of these sizes is crucial when working with simulated data and uesgraphs.
The transformation has not be to understood deeply. Using the newest version of uesgraphs will write the systemmodelgraph into a json file, which can be used by the proper analyze functions to map the data accordingly. The mapping process in more detail is described below:

The Mapping Process
-------------------

1. Identifying Corresponding Elements
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For each node in the UES Graph, we:

- Identify all connected pipes
- Find all connection ports where these pipes meet in the System Model
- Map the uesgraphs node to these connection ports

.. code-block:: text

   uesgraphs node → [Pipe1, Pipe2, ...] → [Port1, Port2, ...]

2. Special Case: Terminal Nodes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Building nodes (demand/supply) represent a special case:

- They connect to only one pipe
- They require special handling to identify the correct ports

3. Validation Process
~~~~~~~~~~~~~~~~~~~~~

The structural validation ensures:

- All uesgraphs nodes are mapped to ports
- Each node has either two connected pipes or is a demand/supply node

Core Functions
--------------

The transformation is implemented through several functions in ``uesgraphs.analyze.data_handling.graph_transformation``:

.. py:function:: map_ues_nodes_to_system_ports(uesgraph, system_model)

   Main function that creates the complete mapping between UES graph nodes and system model ports.

   :param uesgraph: The UESGraph object representing network topology
   :param system_model: The SystemModelHeating object representing the simulation model
   :return: Dictionary mapping UES node IDs to sets of port identifiers

.. py:function:: get_pipes_for_node(graph_sysm, node_id)

   Identifies all pipes connected to a specified node.

   :param graph_sysm: System model graph
   :param node_id: Node identifier
   :return: List of connected pipe IDs

.. py:function:: validate_structural_node_port_mapping(uesgraph, node_to_ports_mapping)

   Validates the structural integrity of the node-to-ports mapping.

Validation Example
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from uesgraphs.analyze.data_handling import graph_transformation as gt

   # Create mapping
   node_port_mapping = gt.map_ues_nodes_to_system_ports(uesgraph, system_model)

   # Validate mapping
   gt.validate_structural_node_port_mapping(uesgraph, node_port_mapping)

The validation function checks:

1. All nodes from the UES graph have a corresponding entry in the mapping
2. Every node has at least two ports assigned (minimum requirement for connections)

.. note::

   This is a structural validation only. It does not verify the actual values or physical correctness of the ports.

Understanding the Transformation
---------------------------------

Physical Intuition
~~~~~~~~~~~~~~~~~~

Think of this mapping as translating between two views of the same physical system:

**The Plumber's View (UES Graph)**:

- Pipes connect at junction points
- Fluid flows through pipes from source to destination

**The Simulator's View (System Model)**:

- Each pipe is a component with internal state
- Components connect at ports with defined properties

Example Scenario
~~~~~~~~~~~~~~~~

Consider a simple T-junction connecting three pipes:

.. code-block:: text

   UES Graph:          System Model:
       P1                P1
        \                 |\
         N -- P3    vs.   | P3
        /                 |
       P2                P2

In the UES Graph, pipes P1, P2, and P3 meet at node N.

In the System Model, pipes P1, P2, and P3 are nodes, with connections (edges) between them.

The mapping finds the pipes P1, P2 and P3 around the desired UESGraph node N first. Since in the system model the UESGraph node N is represented by edges, the edges between P3, P1 and P2 are all different representations of the same node N. The current mapping saves all those edges for node N in a dictionary.

Practical Applications
----------------------

This mapping enables:

1. **Simulation Integration**: Connecting network topology models with physics-based simulations
2. **State Analysis**: Tracking state changes across the entire system
3. **Validation**: Ensuring physical constraints are maintained at connection points
4. **Error Detection**: Identifying inconsistencies in the model structure

Complete Workflow Example
--------------------------

.. code-block:: python

   import uesgraphs as ug
   from uesgraphs.analyze.data_handling import graph_transformation as gt
   from uesgraphs.systemmodels import SystemModelHeating

   # 1. Load or create UESGraph
   graph = ug.UESGraph()
   graph.from_json("district_network.json")

   # 2. IMPORTANT: Save and reload to normalize internal structures
   graph.to_json("normalized_network.json")
   graph = ug.UESGraph()
   graph.from_json("normalized_network.json")

   # 3. Generate system model
   system_model = SystemModelHeating(graph)

   # 4. Create port mapping
   node_port_mapping = gt.map_ues_nodes_to_system_ports(graph, system_model)

   # 5. Validate mapping
   gt.validate_structural_node_port_mapping(graph, node_port_mapping)

   # 6. Use mapping for analysis
   for node_id, ports in node_port_mapping.items():
       print(f"Node {node_id} connects to ports: {ports}")

Implementation Notes
--------------------

When implementing this transformation:

- **Ensure node names are consistent** between graph representations
- **Handle special cases** for terminal nodes (buildings)
- **Validate the structural integrity** of the mapping
- **Save/reload via JSON** before transformation to avoid inconsistencies
- **Consider performance optimizations** for large networks (>100 nodes)

See Also
--------

- :doc:`../guides/model_generation_pipeline` - How to generate Modelica models from UESGraphs
- :py:mod:`uesgraphs.analyze.data_handling.graph_transformation` - API reference
