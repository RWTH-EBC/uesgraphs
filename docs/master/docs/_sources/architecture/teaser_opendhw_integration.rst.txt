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

The TEASER and OpenDHW integration enables the estimations of 
demands necessary for the simulation.

Key Design Principles
~~~~~~~~~~~~~~~~~~~~~

1. **GeoJSON as main file for buildings**: All building properties are 
   stored on in buildings_geojson before estimation.
2. **Excel-based Configuration**: Uniform parameters (simulation setup) 
   are read from Excel sheets.
4. **Traceability**: Every major processing step persists 
   intermediate states of data.

Technology Stack
~~~~~~~~~~~~~~~~

- **Buildings**: GeoJSON file
- **Simulation Engine**: pandapipes
- **Configuration**: Excel or directly
- **Time-Series Data**: CSV files

--------------

Pipeline Architecture
---------------------

High-Level Flow
~~~~~~~~~~~~~~~

TEASER:
::

   GeoJSON
        ↓
   run_sim_teaser
        ↓
   ┌──────────────────────────────────┐
   │ 0. Load simulation settings and  │
   │    set up directories            │
   │ 1. Create TEASER project         │
   │ 2. Temporary directory and       │
   │    AixLib export                 │
   │ 3. Run simulations               │
   │ 4. Read results and save data    │
   │ 5. Combine results for demand CSV│
   └──────────────────────────────────┘
        ↓
   demands-heat.csv
   demands-cool.csv

OpenDHW:
::

   GeoJSON
        ↓
   generate_DHW_profiles_from_geojson
        ↓
   ┌──────────────────────────────────┐
   │ 0. Load simulation settings and  │
   │    set up directories            │
   │ 1. Create DHW profiles           │
   │ 2. Save profiles to CSV          │
   └──────────────────────────────────┘
        ↓
   demands-dhw.csv
-------------

Core Entry Points
----------------

### `run_sim_teaser(...)`

**Location**: ``teaser_integration/utilities.py``
**Responsibility**: End-to-end orchestration of TEASER integration
**Inputs**: GeoJSON, either Excel config or timestep and stoptime,
   weather data
**Outputs**: Heat and cool demand files as CSV

### `generate_DHW_profiles_from_geojson(...)`

**Location**: ``DHW_estimation/utilities.py``
**Responsibility**: End-to-end orchestration of OpenDHW integration
**Inputs**: GeoJSON, either Excel config or timestep, mean draw-off and 
   temperature difference for DHW
**Outputs**: DHW demand file as CSV

TEASER usage
------------

1. TEASER is integrated with creating a TEASER project and assigning the buildings with the propertiers given from the geojson.
   Here archetypes like "OfficeExisting", "OfficeWithDataCenter", "OfficeHighRise", "OfficeHighRiseKita" are set 
   with construction_data= "iwu_heavy" and geometry_data="bmvbs_office".
   For archetype "MultiFamilyHouse" construction_data= "tabula_de_standard" and geometry_data="tabula_de_multi_family_house" and
   for "SingleFamilyHouse" construction_data= "tabula_de_standard" and geometry_data="tabula_de_single_family_house" are set.
   The other properties are set directly. Other archetypes are not allowed in this implementation.
2. Then exporting AixLib, so cloning the repository if necessary and creating temporary directory for the Modelica simulations.
3. Running the simulations with specific simulation architecture in Dymola. 
4. Reading the results and saving the data in a csv files for each building and after that combining the files to one demand csv.

Important notes:
   - Dymola must be installed and Python has to recognize it
   - Since only timestep and stoptime is used, it is not possible to change the start_time, so always start at 0 then.

OpenDHW profiles generation
---------------------------

1. OpenDHW is integrated with creating the profiles for each building with the properties given from the geojson. 
   Here the archetypes like "OfficeExisting", "OfficeWithDataCenter", "OfficeHighRise", "OfficeHighRiseKita" are set 
   with building_type="OB", the archetype "MultiFamilyHouse" is set with building_type="MFH" and "SingleFamilyHouse" are set 
   with building_type="SFH". The other properties are set directly. Other archetypes are not allowed in this implementation.
2. The resulting DataFrame of the profiles is saved in a csv file.

Important notes:
   - Since only timestep, it is not possible to change the start_time nor stop_time, so always start at 0 and stoptime is 
   always set to one year because of OpenDHW's internal architecture.

File & Folder Structure
-----------------------

::

   workspace/
     └── demand_csv/
         ├── demands-cool.csv (from TEASER)
         ├── demands-dhw.csv (from OpenDHW)
         └── demands-heat.csv (from TEASER)

---

Extension Guide
---------------

### Changing initial parameters of TEASER or OpenDHW integration

1. Some parameters could be also set via Excel if necessary

---

*This document describes the architecture of the TEASER and OpenDHW integration in UESGRAPH.*
