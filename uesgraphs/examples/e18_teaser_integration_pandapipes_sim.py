"""
TEASER Integration with pandapipes Simulation using GeoJSON Input
==============================================================

This example demonstrates the workflow if the TEASER integration is used on the example 17.

Main difference:
    - The use of a different geojson which has the information required for TEASER integration
    - The run_sim_teaser function is used to generate the building demands

The run_sim_teaser function generates the heating, DHW, and cooling demand time series files 
based on the building information provided in the GeoJSON file.

Therefore the input parameters:
    - The path to the building GeoJSON file
    - The save path for the generated demand files
Optional parameters:
    - The weather file path for a specific weather scenario over the simulation period
    - The timestep in seconds for the simulation (default is 3600 for hourly data)
    - The stop time in seconds for the simulation (default is 8760*3600 for one year of hourly data)
    - A specific sim_setup_path for TEASER configuration, which is given in the Modelica 
      or pandapipes example (E16 and E17) to set the timestep and stop time accordingly.
"""

import os
import sys
import logging

# Add parent directory to path to ensure imports work from local development
script_dir = os.path.dirname(os.path.abspath(__file__))
uesgraphs_root = os.path.dirname(os.path.dirname(script_dir))
if uesgraphs_root not in sys.path:
    sys.path.insert(0, uesgraphs_root)

from uesgraphs import UESGraph
from uesgraphs.systemmodels_pp.utilities import uesgraph_to_pandapipes
from uesgraphs.teaser_integration.utilities import run_sim_teaser


def workspace_example(name_workspace=None):
    """
    Creates a local workspace with given name (copied from e1_readme_example)

    Parameters
    ----------
    name_workspace : str
        Name of the local workspace to be created

    Returns
    -------
    workspace : str
        Full path to the new workspace
    """
    this_dir = os.path.dirname(__file__)
    ues_dir = os.path.dirname(os.path.dirname(this_dir))
    workspace = os.path.join(ues_dir, "workspace")
    if not os.path.exists(workspace):
        os.mkdir(workspace)

    if name_workspace is not None:
        workspace = os.path.join(workspace, name_workspace)
        if not os.path.exists(workspace):
            os.mkdir(workspace)

    return workspace


def main():
    print("="*80)
    print("E18: GeoJSON to pandapipes simulation")
    print("="*80)

    # =========================================================================
    # STEP 1: Setup Workspace and Paths
    # =========================================================================
    print("\n STEP 1: Setting up workspace and paths...")

    # Create workspace directory for this example
    workspace = workspace_example("e18")
    print(f"   Workspace: {workspace}")

    # Get paths to example data files
    uesgraphs_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(uesgraphs_dir, 'uesgraphs', 'data', 'examples')
    geojson_dir = os.path.join(data_dir, 'e15_geojson')

    # Input file paths
    network_geojson = os.path.join(geojson_dir, 'network.geojson')
    buildings_geojson = os.path.join(geojson_dir, 'buildings_teaser_info.geojson')
    supply_geojson = os.path.join(geojson_dir, 'supply.geojson')

    # Ground temperature file
    ground_temp_path = os.path.join(data_dir, 'ground_temps_hassel.csv')

    # Excel configuration template
    excel_config_path = os.path.join(uesgraphs_dir, 'uesgraphs', 'data',
                                     'uesgraphs_parameters_template_pp.xlsx')

    print("   ✓ All paths configured")

    # =========================================================================
    # STEP 2: Demand estimation simualtion with TEASER
    # =========================================================================

    print("\n  STEP 2: Demand estimation simualtion with TEASER...")

    input_heating, input_dhw, input_cooling = run_sim_teaser(buildings_info_path=buildings_geojson,
                   save_path=workspace,
                   sim_setup_path=excel_config_path,
                   log_level=logging.INFO
                   )

    # =========================================================================
    # STEP 3: Import District Network from GeoJSON
    # =========================================================================
    
    print("\n  STEP 3: Importing district network from GeoJSON files...")
  

    graph = UESGraph()
    graph.from_geojson(
        network_path=network_geojson,
        buildings_path=buildings_geojson,
        supply_path=supply_geojson,
        name='simple_district',
        save_path=workspace,
        generate_visualizations=False
    )

    # Display network statistics
    print(f"\n   GeoJSON import successful!")

    # Save the imported graph
    graph_json_path = os.path.join(workspace, 'simple_district_graph.json')
    graph.to_json(path=workspace, name='simple_district_graph', all_data=True, prettyprint=True)
    print(f"     - Saved graph to: {graph_json_path}")

    # =========================================================================
    # STEP 4: Generate pandapipes simulation results using New Excel-Based Pipeline
    # =========================================================================
    print(f"\n   Excel configuration: {excel_config_path}")
    print(f"   Demand files:")
    print(f"     - Heating: {os.path.basename(input_heating)}")
    print(f"     - DHW: {os.path.basename(input_dhw)}")
    print(f"     - Cooling: {os.path.basename(input_cooling)}")
    print(f"   Ground temperature: {os.path.basename(ground_temp_path)}")

    print("\n   Starting pipeline (this may take a few moments)...\n")

    try:
        # Run the new Excel-based pipeline
        # Note: You can pass either a UESGraph object OR a path to a JSON file
        uesgraph_to_pandapipes(
            uesgraph=graph,                    # UESGraph object (or JSON path string)
            simplification_level=0,            # No simplification (use full network)
            workspace=workspace,               # Output directory
            sim_setup_path=excel_config_path,  # Excel configuration file
            input_heating=input_heating,       # Heating demand time series
            input_dhw=input_dhw,              # DHW demand time series
            input_cooling=input_cooling,       # Cooling demand time series
            ground_temp_path=ground_temp_path, # Ground temperature data
            log_level=logging.INFO            # Logging level (INFO for moderate detail)
        )

        print("\n    SUCCESS: Pandapipes simulation completed!")

    except Exception as e:
        print(f"\n    ERROR: Pipeline failed with: {e}")
        print("    Check the log file for detailed error information")
        raise

    # =========================================================================
    # STEP 5: Summary and Next Steps
    # =========================================================================
    print("\n" + "="*80)
    print(" E18 Example Completed Successfully!")
    print("="*80)

    print(f"\n Output Locations:")
    print(f"   Workspace: {workspace}")
    print(f"   Generated Models: {os.path.join(workspace, 'models')}")

    print(f"\n What was generated:")
    print(f"   - UESGraph JSON file with network topology and attributes")
    print(f"   - pandapipes simulation results in timestamp directory")

    print("\n" + "="*80)



if __name__ == "__main__":
    print("\n" + "="*80)
    print("UESGraphs Example 18: Complete GeoJSON to pandapipes Workflow")
    print("Using the new Excel-based parameter configuration system")
    print("="*80)

    main()

    print("\n" + "="*80)
    print("Example script completed. Check your workspace for outputs!")
    print("="*80 + "\n")
