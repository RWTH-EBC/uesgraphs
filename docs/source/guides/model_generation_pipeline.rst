Model Generation Pipeline
=========================

Generate Modelica simulation models from UESGraph district heating networks using Excel-based configuration.

Quick Start
-----------

**Workflow from GeoJSON to Modelica:**

.. code-block:: python

   import uesgraphs as ug
   from uesgraphs.systemmodels.model_generation_pipeline import uesgraph_to_modelica
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

   # 2. Generate Modelica model
   uesgraph_to_modelica(
       uesgraph=graph,             
       sim_setup_path="config.xlsx",               # Excel configuration
       workspace="./output",                       # Output directory
       simplification_level=0,                     # Network simplification (0 = none)
       input_heating="demands_heating.csv",        # Heating demand profile
       input_dhw="demands_dhw.csv",                # DHW demand profile
       input_cooling="demands_cooling.csv",        # Cooling demand profile
       ground_temp_path="ground_temperature.csv"   # Ground temperature data
   )

This generates a complete Modelica package in ``./output/models/`` ready for simulation.

**If you already have a JSON file:**

.. code-block:: python

   from uesgraphs.systemmodels.model_generation_pipeline import uesgraph_to_modelica

   uesgraph_to_modelica(
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
   - Created from GeoJSON, OSM, or manually

   .. seealso::

      - **GeoJSON Import**: See :doc:`../api_examples` (Example 15: Import from GeoJSON)
      - **Known Issues**: `GitHub Issue #69 <https://github.com/RWTH-EBC/uesgraphs/issues/69>`_ for GeoJSON import improvements

2. **Excel Configuration** (``uesgraphs_parameters_template.xlsx``)

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

Generated Modelica package in timestamped directory:

.. code-block:: text

   workspace/models/Sim20250121_143022_MyProject/
   ├── Sim20250121_143022_MyProject.mo    # Main model file
   ├── package.mo                          # Package definition
   ├── package.order                       # Load order
   └── Resources/Inputs/                   # CSV input files

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
solver                Cvode          -      Modelica solver (Cvode, Dassl, etc.)
start_time            0              s      Simulation start time
stop_time             31536000       s      Simulation end time (1 year)
timestep              900            s      Time resolution (15 min)
tolerance             1e-6           -      Solver tolerance
===================== ============== ====== =====================================

Pipes Sheet
~~~~~~~~~~~

Parameters for pipe components.

===================== ============== ====== =====================================
Parameter             Example Value  Unit   Description
===================== ============== ====== =====================================
template              AixLib.Fluid.. -      Modelica template name
diameter              @diameter      m      Pipe inner diameter (from graph)
roughness             2.5e-5         m      Surface roughness
dp_nominal            0.1            bar    Nominal pressure drop
===================== ============== ====== =====================================

Supply Sheet
~~~~~~~~~~~~

Parameters for supply station components.

===================== ============== ====== =====================================
Parameter             Example Value  Unit   Description
===================== ============== ====== =====================================
template              AixLib.Fluid.. -      Modelica template name
TIn                   353.15         K      Supply temperature (constant)
dpIn                  150000         Pa     Pressure difference
===================== ============== ====== =====================================

Demands Sheet
~~~~~~~~~~~~~

Parameters for demand substation components.

===================== ============== ====== =====================================
Parameter             Example Value  Unit   Description
===================== ============== ====== =====================================
template              AixLib.Fluid.. -      Modelica template name
Q_flow_nominal        @Q_flow_nominal W     Nominal heat flow (from graph)
TReturn               313.15         K      Return temperature
dTDesign              30             K      Design temperature difference
===================== ============== ====== =====================================

.. note::

   **@References**: Parameters starting with ``@`` reference graph attributes.

   Example: ``@diameter`` reads the ``diameter`` attribute from each edge in your graph.

Parameter Priority
------------------

When a parameter is defined in multiple places, the pipeline uses this priority order (highest to lowest):

**1. Graph attributes** (your UESGraph)

   Values you set directly in your graph always take precedence.

   .. code-block:: python

      graph.edges[e1, e2]['dp_nominal'] = 0.05  # This value wins!

**2. Excel values** (configuration file)

   Default values from your Excel configuration.

   .. code-block:: text

      Excel Pipes Sheet:
      dp_nominal = 0.1

**3. Modelica defaults** (built-in)

   For optional (AUX) parameters only. If neither graph nor Excel has a value, Modelica uses its built-in default.

**Example:**

.. code-block:: python

   # Scenario:
   # - Graph: dp_nominal = 0.05
   # - Excel: dp_nominal = 0.1
   # - Modelica default: 0.0

   # Result: dp_nominal = 0.05  ← Graph wins!

This allows you to:

- Set **general defaults** in Excel (applied to all components)
- Override **specific components** in your graph (component-specific values)
- Rely on **Modelica defaults** for optional parameters you don't care about

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

**Template not found**

   Template name in Excel doesn't match filename. Check:

   - Template files in ``uesgraphs/data/templates/network/{pipe,supply,demand}/``
   - Exact filename (without ``.mako`` extension)

Debug Mode
~~~~~~~~~~

Enable detailed logging:

.. code-block:: python

   import logging

   uesgraph_to_modelica(
       ...,
       log_level=logging.DEBUG  # Shows all processing steps
   )

See Also
--------

- :doc:`../architecture/modelica_pipeline` - Technical architecture details
- :doc:`hydronic_sizing` - How to size your network before model generation
- :doc:`../architecture/graph_transformation` - Mapping simulation results back to UESGraph
