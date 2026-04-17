Heat and DHW Demand Estimation
=========================

Generate Heat and DHW estimation profiles, which can be used in the simulations with uesgraphs.

Quick Start
-----------

**Workflow from GeoJSON information to demands:**

.. code-block:: python

   import uesgraphs as ug
   from uesgraphs.teaser_integration.utilities import run_sim_teaser
   from uesgraphs.DHW_estimation.utilities import generate_DHW_profiles_from_geojson

   # Estimate heat demand with TEASER
   input_heating, input_cooling = run_sim_teaser(
            buildings_info_path=buildings_geojson, # geojson with necessary building attributes
            save_path=workspace, # output directory for generated files
            sim_setup_path=excel_config_path, # optional Excel file for TEASER settings
            log_level=logging.INFO # log_level
            )

   # Estimate demand with OpenDHW
   input_dhw = generate_DHW_profiles_from_geojson(
            buildings_info_path=buildings_geojson, # geojson with necessary building attributes
            save_path=workspace, # output directory for generated files
            sim_setup_path=excel_config_path, # optional Excel file for OpenDHW settings
            log_level=logging.INFO # log_level
      ) 

This generates the demand profiles in CSV format, which can be directly used in the pandapipes simulation workflow.

**If you are not using the excel config:**

.. code-block:: python

   from uesgraphs.teaser_integration.utilities import run_sim_teaser
   from uesgraphs.DHW_estimation.utilities import generate_DHW_profiles_from_geojson

   # Estimate heat demand with TEASER
   input_heating, input_cooling = run_sim_teaser(
            buildings_info_path=buildings_geojson, 
            save_path=workspace, # output directory for generated files
            weather_path=None, # Optional, weather data for TEASER (if None, uses default weather data)
            timestep=3600, # timestep for the generated profiles (in seconds)
            stop_time=8760*3600, # total simulation time (1 year in seconds)
            log_level=logging.INFO
            )

   # Estimate demand with OpenDHW
   input_dhw = generate_DHW_profiles_from_geojson(
            buildings_info_path=buildings_geojson, 
            save_path=workspace, 
            timestep=3600, # timestep for the generated profiles (in seconds)
            mean_drawoff_vol_per_day=40, # Mean drawoff volume per day (liters) for DHW estimation (default 40 L/day)
            temp_dT_dhw=35, # Temperature difference for DHW estimation (default 35 K)
            log_level=logging.INFO
            )
   
Important to notice that OpenDHW always produces data for a year,
while TEASER can be configured for different time periods.

What You Need
-------------

**Required Files:**

**GEOJSON** for the buildings which should have these attributes:

   TEASER:
      - "archetype" (e.g. MultiFamilyHouse, SingleFamilyHouse, OfficeExisting etc.)
      - "year_of_construction" (e.g. 1990, 2005, 2010 etc.)
      - "height_of_floors" (e.g. 3.0, 3.5 etc.)
      - "number_of_floors" (e.g. 2, 3, 4 etc.)
      - "net_leased_area" (e.g. 7051, 9890 etc.)
      - "with_ahu" (True/False) - For Air Handling unit, default False
      - "internal_gains_mode" (e.g. 2) - internal gains mode for TEASER, default 2
   
   OpenDHW:
      - "archetype" (e.g. MultiFamilyHouse, SingleFamilyHouse, OfficeExisting etc.) same as in TEASER
      - "occupants" (e.g. 4 for a family of 4, 1 for single occupant etc.)
   
   .. seealso::
      
      - **TEASER**: See TEASER documentation http://rwth-ebc.github.io/TEASER/ for further information about the attributes.
      - **OpenDHW**: See OpenDHW documentation https://github.com/RWTH-EBC/OpenDHW/blob/main/Doc/doc.md for further information about the attributes.

**Output:**

Generated pandapipes results in timestamped directory:

.. code-block:: text

   workspace/demand_csv/
   ├── demands-cool.csv    # Cooling demands (for now default 0)
   ├── demands-dhw.csv     # DHW demands with timestamps and building name in columns
   └── demands-heat.csv    # Heating demands with timestamps and building name in columns


If Excel Configuration used then these important parameters must be set in the corresponding sheets:
-------------------

The Excel file has **4 sheets**:

Simulation Sheet
~~~~~~~~~~~~~~~~

Global simulation settings.

========================= ============== ====== =====================================
Parameter                 Example Value  Unit   Description
========================= ============== ====== =====================================
simulation_name           MyProject      -      Name for the generated model
stop_time                 31536000       s      Simulation end time (1 year)
timestep                  3600           s      Time resolution (1 hour)
temp_dT_dhw               35             K      Temperature difference for DHW estimation (default 35 K)
mean_drawoff_vol_per_day  40             L/day  Mean drawoff volume per person per day for DHW estimation (default 40 L/day)
========================= ============== ====== =====================================

See Also
--------

- :doc:`../architecture/OpenDHW_TEASER_int` - Technical architecture details