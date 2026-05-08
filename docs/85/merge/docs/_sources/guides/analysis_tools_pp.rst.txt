Analysis of pandapipes simulation results with UESGraph return and supply side graphs
=====================================================================================

Generates analysis calculations or plots for deeper insights on the simulation results.

Quick Start
-----------

**Workflow from GeoJSON to Pandapipes:**

.. code-block:: python

   from uesgraphs.analyze.analysis_pp import analysis_pp

   # 1. Import network from GeoJSON
   sim_path = os.path.join(workspace, "models", "Sim20260402_101253")

   # 2. Generate pandapipes simulation
   analysis = analysis_pp(root_path=Path(sim_path))

   # Calculates for all pipes the timestep with the maximum heat loss and the total heat loss over the simulation period
   analysis.thermal_loss_analysis()

   # Calculates for the supply pumps the maximum power at a given time step and the total energy consumption over the simulation period
   analysis.pump_power_analysis()
   
   # Generates for each pipe a plot of mass flow, pressure drop, temperature in and out and heat loss over time
   analysis.pipe_plots() 

   # Retransforms the mass flow, in- and oultet temperatures and heat loss for all pipes to the geojson
   analysis.retransform_pipe_geojson_data(Path(sim_path) /"network_full_new_simulation.geojson") 

   # Visualizes the mass flow, pressure drops, temperatures and pressures for the supply and return side in the network at a specific time step
   analysis.visualize_network_results(time_index=10)

This analysis workflow allows you to extract detailed insights from your pandapipes simulations, focusing on thermal losses and pump performance. 

What You Need
-------------

**Required Files:**

1. **UESGraph** (JSON format)

   - Network topology with nodes and edges with the data
   - Created from previous simulations, should contain all simulated variables for the nodes and edges (e.g. pressure, temperature, mass flow, etc.)  

2. **Network of pipes** (GeoJSON format)

   - network.json which has all pipes included, only used in the retransformation of the pipe data to this specific geojson

**Output:**

Generated pandapipes results in timestamped directory:

.. code-block:: text

   workspace/models/Sim20250121_143022/analysis_outputs
   ├── geojsons
      ├── network_R_data.geojson       # Return side pipes results
      └── network_S_data.geojson       # Supply side pipes results
   ├── network_visualization
      ├── dp_R.png                     # Return side pressure drops
      ├── dp.png                       # Supply side pressure drops
      ├── m_flow_R.png                 # Return side mass flows
      ├── m_flow.png                   # Supply side mass flows
      ├── pressure_R.png               # Return side pressures
      ├── pressure.png                 # Supply side pressures
      ├── temperature_R.png            # Return side temperatures
      └── temperature.png              # Supply side temperatures
   └── pipe_plots                      # Following plots for each pipe (supply and return side):
      ├── pipe_m_flow_10011026.png     # Mass flow pipe plot
      ├── pipe_Q_loss_10011026.png     # Heat loss pipe plot
      ├── pipe_temp_df_10011026.png    # Temperture difference pipe plot
      ├── R_pipe_m_flow_10011026.png   # Mass flow pipe plot for return side
      ├── R_pipe_Q_loss_10011026.png   # Heat loss pipe plot for return side
      └── R_pipe_temp_df_10011026.png  # Temperture difference pipe plot for return side

See Also
--------

- :doc:`../architecture/pandapipes_pipeline` - Technical details on the pandapipes pipeline and the generated data
