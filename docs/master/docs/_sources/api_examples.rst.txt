Examples
========

Python Script Examples
----------------------

.. autosummary::
   :toctree: _autosummary

   uesgraphs.examples.e1_readme_example
   uesgraphs.examples.e2_simple_dhc_example
   uesgraphs.examples.e3_add_network_example
   uesgraphs.examples.e4_save_uesgraphs_example
   uesgraphs.examples.e5_add_street_nodes_example
   uesgraphs.examples.e6_additional_building_attributes_example
   uesgraphs.examples.e7_plot_uesgraphs_example
   uesgraphs.examples.e8_load_uesgraphs_example
   uesgraphs.examples.e9_generate_ues_from_osm_example
   uesgraphs.examples.e10_networks_example
   uesgraphs.examples.e11_model_generation_example
   uesgraphs.examples.e12_template_generation_example

Example 13: Analysis and Visualization of Simulation Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: uesgraphs.examples.e13_analyze_uesgraphs_example
   :members:
   :undoc-members:
   :show-inheritance:

This example processes and visualizes simulation results from Dymola for UESGraphs-generated 
district heating network models. It demonstrates the analysis workflow from loading 
simulation data to creating network visualizations with key performance indicators.

**Prerequisites:**

- Simulation period can be specified (default: one week)
- Visualization uses time-averaged values for certain properties
- AixLib version must be specified for correct data mapping
- All paths are relative to the workspace directory

**Location:** ``uesgraphs/examples/e13_analyze_uesgraphs_example.py``

**GitHub:** `View on GitHub <https://github.com/RWTH-EBC/uesgraphs/blob/master/uesgraphs/examples/e13_analyze_uesgraphs_example.py>`_

Jupyter Notebook Examples
--------------------------

Example 14: Hydronic Sizing Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This interactive notebook demonstrates demand-based mass flow estimation and hydronic sizing capabilities.

**Topics covered:**

- Physically accurate mass flow calculations based on individual demand nodes
- Automated pipe sizing using manufacturer catalogs
- Robust network design using maximum flow principles
- Flexible scenario analysis (peak vs average loads)

**Location:** ``uesgraphs/examples/e14_hydronic_sizing_example.ipynb``

**GitHub:** `View on GitHub <https://github.com/RWTH-EBC/uesgraphs/blob/master/uesgraphs/examples/e14_hydronic_sizing_example.ipynb>`_

Interactive Plotting Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Additional interactive plotting demonstrations using Jupyter notebooks.

**Location:** ``uesgraphs/examples/interactive_plotting_example.ipynb``

**GitHub:** `View on GitHub <https://github.com/RWTH-EBC/uesgraphs/blob/master/uesgraphs/examples/interactive_plotting_example.ipynb>`_
