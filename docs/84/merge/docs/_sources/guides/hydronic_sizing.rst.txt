Hydraulic Network Sizing
========================

A physics-based approach for automated mass flow calculation and pipe sizing in district heating networks.

Quick Start
-----------

.. code-block:: python

   import uesgraphs as ug
   import uesgraphs.systemmodels.utilities as sysm_ut

   # 1. Load your network
   graph = ug.UESGraph()
   graph.from_json("network.json", network_type="heating")

   # 2. Set demand data and temperature differences
   for node in graph.nodelist_building:
       if not graph.nodes[node].get("is_supply_heating", False):
           graph.nodes[node]["input_heat"] = 15000  # W (example: 15 kW peak load)
           graph.nodes[node]["dT_Network"] = 30.0   # K

   # 3. Size the network
   sized_graph = sysm_ut.size_hydronic_network(
       graph=graph,
       catalog="isoplus",
       load_scenario="peak_load"
   )

   # 4. Analyze results
   for edge in sized_graph.edges:
       data = sized_graph.edges[edge]
       print(f"Pipe {edge}: {data['DN']}, {data['m_flow_peak_load']:.3f} kg/s")

.. note::

   The function accepts both **scalar values** and **time-series** for ``input_heat``:

   - **Scalar**: ``graph.nodes[node]["input_heat"] = 15000`` (single peak load value)
   - **Time-series**: ``graph.nodes[node]["input_heat"] = [1000, 5000, 15000, ...]`` (automatically extracts peak/average based on ``load_scenario``)

Prerequisites
-------------

Your graph needs these node attributes:

- **input_heat**: Thermal demand [W] at each consumer node
- **dT_Network**: Temperature difference [K] between supply and return
- **is_supply_heating**: Boolean flag to identify supply nodes

How it Works
------------

1. Demand-Based Mass Flow Calculation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The system calculates mass flows starting at consumer nodes using the fundamental equation:

.. math::

   \dot{m} = \frac{Q}{c_p \cdot \Delta T}

Where:

- **Q**: Thermal load [W]
- **cp**: Specific heat capacity (4184 J/kg·K for water)
- **ΔT**: Temperature difference [K]

2. Flow Path Aggregation
~~~~~~~~~~~~~~~~~~~~~~~~~

Mass flows are aggregated backward through the network:

- Identifies all supply-to-demand paths
- Accumulates flows along each path
- Applies maximum flow principle for robust sizing

3. Catalog-Based Pipe Selection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Matches calculated flows to real pipe diameters:

- Uses manufacturer catalogs (e.g., Isoplus)
- Selects next larger pipe if no exact match
- Adds ``DN`` (nominal diameter) and ``diameter`` [m] attributes to edges

Core Functions
--------------

Mass Flow Calculation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Calculate mass flows based on demand
   graph = sysm_ut.estimate_m_flow_demand_based(
       graph=graph,
       network_type="heating",
       demand_attribute="input_heat",
       load_scenario="peak_load",  # or "average_load"
       dT_attribute="dT_Network"
   )

**Key features:**

- Scenario-based calculations (peak vs. average load)
- Individual temperature differences per node
- Robust path-based flow aggregation

Complete Hydraulic Sizing
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Full workflow: mass flows + pipe diameters
   graph = sysm_ut.size_hydronic_network(
       graph=graph,
       catalog="isoplus",
       dT_attribute="dT_Network",
       network_type="heating",
       load_scenario="peak_load"
   )

Output Attributes
-----------------

After sizing, edges contain:

- **m_flow_peak_load** or **m_flow_average_load**: Mass flow [kg/s]
- **DN**: Nominal diameter designation (e.g., "DN50")
- **diameter**: Inner pipe diameter [m]

Learn More
----------

For detailed examples, see the comprehensive tutorial notebook: :doc:`../api_examples` (Example 14: Hydronic Sizing).

Advanced Features
-----------------

- **Custom pipe catalogs**: Add your own manufacturer data
- **Multiple scenarios**: Compare peak vs. average sizing
- **Temperature flexibility**: Different ΔT per building type
- **Visualization**: Integrated diameter plotting with ``uesgraphs.visuals``

.. note::

   This feature replaces the deprecated ``estimate_m_flow_nominal()`` function with a more accurate demand-based approach.
