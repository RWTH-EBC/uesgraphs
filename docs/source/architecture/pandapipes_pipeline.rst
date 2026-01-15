UESGraphs pandapipes simulation Pipeline
===========================================

Architecture Documentation
--------------------------

**Version:** --- **Last Updated:** ---

--------------

Table of Contents
-----------------

1. `Overview <#overview>`__
2. `Pipeline Architecture <#pipeline-architecture>`__
3. `Core Entry Point <#core-entry-point>`__
4. `Parameter Assignment Flow <#parameter-assignment-flow>`__
5. `Demand & Time-Series Handling <#demand--time-series-handling>`__
6. `pandapipes Model Generation <#pandapipes-model-generation>`__
7. `File & Folder Structure <#file--folder-structure>`__
8. `Validation & Error Handling <#validation--error-handling>`__
9. `Extension Guide <#extension-guide>`__

--------------

Overview
--------

The UESGraphs pandapipes simulation pipeline enables the execution of
thermo-hydraulic network simulations based on the graph-structure.

Key Design Principles
~~~~~~~~~~~~~~~~~~~~~

1. **Graph as Single Source of Truth**: All topology, parameters and 
   time-series references are stored on the UESGraph before model generation
2. **Excel-based Configuration**: Uniform parameters (pipes, supply, demand,
   simulation setup) are read from Excel sheets
3. **Fail Early**: Missing files, invalid graphs or inconsistent parameters 
   abort the pipeline with explicit error messages
4. **Traceability**: Every major processing step persists 
   intermediate graph states to JSON

Technology Stack
~~~~~~~~~~~~~~~~

- **Graph Representation**: NetworkX-based UESGraph
- **Simulation Engine**: pandapipes
- **Configuration**: Excel (openpyxl)
- **Time-Series Data**: CSV files

--------------

Pipeline Architecture
---------------------

High-Level Flow
~~~~~~~~~~~~~~~

::

   UESGraph / JSON
        ↓
   uesgraph_to_pandapipes
        ↓
   ┌─────────────────────────────────┐
   │ 1. Validate input paths         │
   │ 2. Load simulation settings     │
   │ 3. Normalize UESGraph           │
   │ 4. Assign demands               │
   │ 5. Assign pipe parameters       │
   │ 6. Assign supply parameters     │
   │ 7. Assign demand parameters     │
   │ 8. Load ground temperature      │  
   │ 9. Generate pandapipes model    │
   └─────────────────────────────────┘
        ↓
   pandapipes Results

-------------

Core Entry Point
----------------

### `uesgraph_to_pandapipes(...)`

**Location**: ``systemmodels_pp/utilities.py``
**Responsibility**: End-to-end orchestration of pandapipes simulations
**Inputs**: UESGraph or JSON path, Excel config, demand CSVs, ground
  temperature data
**Outputs**: Timestamped directory with pandapipes files

----------------

Parameter Assignment Flow
-------------------------

### Execution Order

::

   1. Demand data assignment
   2. Pipe parameters (Excel: "Pipes")
   3. Supply parameters (Excel: "Supply")
   4. Demand parameters (Excel: "Demands")

---

### Pipe Parameters

Assigned to **edges**:

- `dIns`
- `kIns`
- `roughness`
- `ground_depth`
- `sections`

Source: Excel sheet **"Pipes"**  
Missing values fall back to hardcoded defaults.

---

### Supply Parameters

Applied to **building nodes** flagged as supply:

```python
is_supply_heating == True
```

Assigned attributes:

- `TIn`
- `TReturn`
- `dpIn`
- `pReturn`
- `dpFlow`

Unit conversions (Pa → bar) are handled explicitly in the pipeline.

The total number of supplies is stored as:

```python
uesgraph.graph["number_of_supplies"]
```

---

### Demand Parameters

Applied to **non-supply building nodes**:

- `dTDesign`
- `TReturn`
- `cp_default`

Additionally, network-wide defaults are stored on graph level:

```python
uesgraph.graph["dT_Net"]
uesgraph.graph["cp_default"]
```

---

Demand & Time-Series Handling
-----------------------------

### Demand Assignment

Demand CSVs are mapped via:

```python
assign_demand_data(uesgraph, {
    "heating": input_heating,
    "cooling": input_cooling,
    "dhw": input_dhw
})
```

Result:

- Time-series are attached as **graph node attributes**
- Naming conventions are preserved for downstream processing

### Ground Temperature

Ground temperature CSV is loaded once and later sliced by **ground
depth**, defined in the simulation Excel:

```python
ground_temp_list = ground_temp_df[ground_depth].tolist()
```

---


pandapipes Model Generation
---------------------------

### Model Directory Creation

Each simulation run creates a timestamped folder:

::

   workspace/
     └── models/
         └── SimYYYYMMDD_HHMMSS/

### Model Generation

The final pandapipes model is created via:

```python
generate_simulation_model(
    uesgraph,
    sim_name,
    sim_params,
    ground_temp_list,
    sim_model_dir
)
```

**Responsibilities of `generate_simulation_model`:**

- Convert UESGraph → pandapipes net
- Create pipes, junctions, sinks, sources
- Assign thermal & hydraulic parameters
- Attach time-series data
- Execute simulation

**Used components**:

- pandapipes.pipe
- pandapipes.heat_consumer
- pandapipes.circ_pump_pressure
- pandapipes.circ_pump_mass (if multiple supplies)
- pandapipes.junction

**Solver Settings**:

- mode: 'bidirectional'
- iter: 100

---

File & Folder Structure
-----------------------

::

   workspace/
     ├── uesgraphs_origin.json
     ├── uesgraphs_with_demand.json
     ├── uesgraphs_simplified.json
     └── models/
         └── Sim20250115_101530_MySimulation/
             ├── uesgraphs.json
             ├── [component models]
             └── setup_params.csv   (optional)

---

Validation & Error Handling
---------------------------

### Validation Levels

1. **File System**
   - Missing files → abort

2. **Graph Consistency**
   - Missing edge names → auto-generated
   - Invalid graph type → abort

3. **Excel Parsing**
   - Missing sheets → abort
   - Missing values → defaults or error (depending on context)

4. **Simulation Generation**
   - pandapipes errors are logged and re-raised

### Logging Strategy

- DEBUG: Detailed processing steps
- INFO: Pipeline milestones
- ERROR: Abort conditions

---

Extension Guide
---------------

### Adding New Parameters

1. Add attribute to UESGraph (node or edge)
2. Reference or override via Excel
3. Ensure `generate_simulation_model` consumes the parameter

---

*This document describes the architecture of the UESGraphs pandapipes simulation pipeline.*
