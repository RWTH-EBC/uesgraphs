Model Generation Pandapipes
=========================

Generate pandapipes simulation models from UESGraph district heating networks using Excel-based configuration.

Quick Start
-----------

**Workflow from GeoJSON to Pandapipes:**

.. code-block:: python

   import uesgraphs as ug
   from uesgraphs.systemmodels_pp.utilities import uesgraph_to_pandapipes
   import uesgraphs.systemmodels.utilities as sysm_ut

   # 1. Import network from GeoJSON
   graph = ug.UESGraph()
   graph.from_geojson(
        network_path=network_geojson,
        buildings_path=buildings_geojson,
        supply_path=supply_geojson,
        name='simple_district',
        save_path="./output",
        generate_visualizations=False
    )

   # 2. Generate pandapipes simulation
   uesgraph_to_pandapipes(
       uesgraph=graph,             
       sim_setup_path="config.xlsx",               # Excel configuration
       workspace="./output",                       # Output directory
       simplification_level=0,                     # Network simplification (0 = none)
       input_heating="demands_heating.csv",        # Heating demand profile
       input_dhw="demands_dhw.csv",                # DHW demand profile
       input_cooling="demands_cooling.csv",        # Cooling demand profile
       ground_temp_path="ground_temperature.csv"   # Ground temperature data
   )

This generates a complete static pandapipes simulation and its results.

**If you already have a JSON file:**

.. code-block:: python

   from uesgraphs.systemmodels_pp.utilities import uesgraph_to_pandapipes

   uesgraph_to_pandapipes(
       uesgraph="network.json",        # Your existing JSON file
       sim_setup_path="config.xlsx",
       workspace="./output",
       simplification_level=0,
       input_heating="demands_heating.csv",
       input_dhw="demands_dhw.csv",
       input_cooling="demands_cooling.csv",
       ground_temp_path="ground_temperature.csv"
   )

What You Need
-------------

**Required Files:**

1. **UESGraph** (JSON format)

   - Network topology with nodes and edges
   - Created from GeoJSON or manually

   .. seealso::

      - **GeoJSON Import**: See :doc:`../api_examples` (Example 15: Import from GeoJSON)
      - **Known Issues**: `GitHub Issue #69 <https://github.com/RWTH-EBC/uesgraphs/issues/69>`_ for GeoJSON import improvements

2. **Excel Configuration** (``uesgraphs_parameters_template_pp.xlsx``)

   - Simulation settings (solver, duration, timestep)
   - Component parameters (pipes, supply, demand)

3. **Demand Data** (CSV files)

   - Heating demand profile (W)
   - DHW demand profile (W)
   - Cooling demand profile (W)
   - One row per timestep

4. **Ground Temperature** (CSV file)

   - Temperature profile (K)
   - Same timesteps as demand data

**Output:**

Generated pandapipes results in timestamped directory:

.. code-block:: text

   workspace/models/Sim20250121_143022_MyProject/
   ├── res_circ_pump_pressure    # Main pump results
   ├── res_heat_consumer         # Buildings results
   ├── res_junctions             # Junction results 
   ├── res_pipe                  # Pipe results   
   ├── mappings.pkl              # pandapipes mappings
   └── uesgraphs.json            # UESGraph with results

Excel Configuration
-------------------

The Excel file has **4 sheets**:

Simulation Sheet
~~~~~~~~~~~~~~~~

Global simulation settings.

===================== ============== ====== =====================================
Parameter             Example Value  Unit   Description
===================== ============== ====== =====================================
simulation_name       MyProject      -      Name for the generated model
start_time            0              s      Simulation start time
stop_time             31536000       s      Simulation end time (1 year)
timestep              3600           s      Time resolution (15 min)
===================== ============== ====== =====================================

Pipes Sheet
~~~~~~~~~~~

Parameters for pipe components.

===================== ============== ====== =====================================
Parameter             Example Value  Unit   Description
===================== ============== ====== =====================================
dIns                  0.04           m      Thickness of pipe insulation
kIns                  0.03           m      Heat conductivity of pipe insulation
roughness             2.5e-5         m      Surface roughness
ground_depth          1.0            m      Depth of pipe below ground
sections              5              -      Number of pipe sections in simulation
===================== ============== ====== =====================================

Supply Sheet
~~~~~~~~~~~~

Parameters for supply station components.

===================== ============== ====== =====================================
Parameter             Example Value  Unit   Description
===================== ============== ====== =====================================
TIn                   353.15         K      Supply temperature (constant)
pIn                   230000         Pa     Supply pressure (constant)
dpFlow                30000          Pa     Pressure lift (constant)
===================== ============== ====== =====================================

Demands Sheet
~~~~~~~~~~~~~

Parameters for demand substation components.

===================== ============== ====== =====================================
Parameter             Example Value  Unit   Description
===================== ============== ====== =====================================
TReturn               323.15         K      Return temperature
dTNetwork             30             K      Design temperature difference
===================== ============== ====== =====================================

.. note::

   **@References**: Parameters starting with ``@`` reference graph attributes.

   Example: ``@diameter`` reads the ``diameter`` attribute from each edge in your graph.

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**"Required MAIN parameter missing"**

   Excel doesn't have this parameter. Add it to the corresponding sheet (Pipes/Supply/Demands).

**"Attribute not found" for @reference**

   Graph doesn't have this attribute. Either:

   - Add it to your graph: ``graph.nodes[node]['attr_name'] = value``
   - Change Excel to use a direct value instead of ``@attr_name``

**"Connector not linked"**

   Wrong attribute name convention. For demand connectors:

   - ``Q_flow_input`` expects ``input_heat`` in graph
   - ``Q_flow_cool`` expects ``input_cool`` in graph
   - ``Q_flow_dhw`` expects ``input_dhw`` in graph

**CSV files have wrong length**

   Demand and ground temperature CSV files must have the same number of timesteps.

   Calculate expected rows: ``(stop_time / timestep) + 1``

Debug Mode
~~~~~~~~~~

Enable detailed logging:

.. code-block:: python

   import logging

   uesgraph_to_pandapipes(
       ...,
       log_level=logging.DEBUG  # Shows all processing steps
   )

See Also
--------

- :doc:`../architecture/pandapipes_pipeline` - Technical architecture details
- :doc:`hydronic_sizing` - How to size your network before model generation
