"""
GeoJSON Import to Modelica Code Generation
==============================================================

This example demonstrates the workflow for generating modelica simulation files.

=== Main lesson: Know your template! ===

The pipeline checks, which parameters are required for each component template. Following
parameters are read from template:
- MAIN, 
- AUX and 
- CONNECTOR

Those parameters have to be provided either via graph attributes, excel template or references.
This example shows how to use it.



Workflow Overview:
-----------------
1. **GeoJSON Import**: Load network topology, buildings, and supply stations from GeoJSON files
2. **Demand Data Assignment**: Attach heating, DHW, and cooling demand time series to buildings
3. **Excel-Based Configuration**: Use Excel template to configure all simulation and component parameters
4. **Modelica Generation**: Automatically generate ready-to-simulate Modelica code

Excel Configuration Structure:
------------------------------
The Excel template has four sheets:
1. **Simulation**: Simulation parameters (solver, time settings, medium, etc.)
2. **Pipes**: Pipe network parameters (template, insulation, roughness, etc.)
3. **Supply**: Supply station parameters (template, max heat demand, pressures, etc.)
4. **Demands**: Demand substation parameters (template, temperatures, heat exchanger settings, etc.)

Input Data Requirements:
-----------------------
- **Network GeoJSON**: LineString features representing the pipe network
- **Buildings GeoJSON**: Point or Polygon features for demand buildings
- **Supply GeoJSON**: Point features for supply stations (with is_supply_heating=True)
- **Demand CSVs**: Time series for heating, DHW, and cooling demands (8760 hourly values)
- **Ground Temperature CSV**: Ground temperature profiles at various depths

Example Directory Structure:
----------------------------
workspace/e16/
├── simple_district_graph.json          # Saved UESGraph after GeoJSON import
├── models/                             # Generated Modelica files
│   └── Sim20250102_123456_MySimulation/
│       ├── MySimulation.mo             # Main Modelica model
│       ├── package.mo                  # Modelica package definition
│       └── [component models]          # Individual component files
└── [demand and ground temp CSVs]       # Input time series data

Notes:
-----
- The pipeline automatically handles parameter assignment and validation
- Missing buildings in demand files will use dummy demand profiles
- The Excel template can be customized for different simulation scenarios
- Generated Modelica models are compatible with Dymola and require AixLib library
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
from uesgraphs.systemmodels.model_generation_pipeline import uesgraph_to_modelica


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
    print("E16: GeoJSON to Modelica Code Generation")
    print("="*80)

    # =========================================================================
    # STEP 1: Setup Workspace and Paths
    # =========================================================================
    print("\n📁 STEP 1: Setting up workspace and paths...")

    # Create workspace directory for this example
    workspace = workspace_example("e16")
    print(f"   Workspace: {workspace}")

    # Get paths to example data files
    uesgraphs_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(uesgraphs_dir, 'uesgraphs', 'data', 'examples')
    geojson_dir = os.path.join(data_dir, 'e15_geojson')

    # Input file paths
    network_geojson = os.path.join(geojson_dir, 'network.geojson')
    buildings_geojson = os.path.join(geojson_dir, 'buildings.geojson')
    supply_geojson = os.path.join(geojson_dir, 'supply.geojson')

    # Demand and ground temperature files
    input_heating = os.path.join(data_dir, 'demands-heat.csv')
    input_dhw = os.path.join(data_dir, 'demands-dhw.csv')
    input_cooling = os.path.join(data_dir, 'demands-cool.csv')
    ground_temp_path = os.path.join(data_dir, 'ground_temps_hassel.csv')

    # Excel configuration template
    excel_config_path = os.path.join(uesgraphs_dir, 'uesgraphs', 'data',
                                     'uesgraphs_parameters_template.xlsx')

    print("   ✓ All paths configured")

    # =========================================================================
    # STEP 2: Import District Network from GeoJSON
    # =========================================================================
    print("\n  STEP 2: Importing district network from GeoJSON files...")
  

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
    # STEP 3: Generate Modelica Code using New Excel-Based Pipeline
    # =========================================================================
    print("\n  STEP 3: Generating Modelica code using Excel-based pipeline...")
    print("   The pipeline will now:")
    print("   1. Validate/generate edge names (required for Modelica)")
    print("   2. Load simulation settings from Excel 'Simulation' sheet")
    print("   3. Assign heating, DHW, and cooling demand data to building nodes")
    print("   4. Assign pipe parameters from Excel 'Pipes' sheet")
    print("   5. Assign supply station parameters from Excel 'Supply' sheet")
    print("   6. Assign demand substation parameters from Excel 'Demands' sheet")
    print("   7. Validate all required (MAIN) parameters are present")
    print("   8. Generate Modelica model files with timestamped directory")
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
        uesgraph_to_modelica(
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

        print("\n    SUCCESS: Modelica code generation completed!")

    except Exception as e:
        print(f"\n    ERROR: Pipeline failed with: {e}")
        print("    Check the log file for detailed error information")
        raise

    # =========================================================================
    # STEP 4: Summary and Next Steps
    # =========================================================================
    print("\n" + "="*80)
    print(" E16 Example Completed Successfully!")
    print("="*80)

    print(f"\n Output Locations:")
    print(f"   Workspace: {workspace}")
    print(f"   Generated Models: {os.path.join(workspace, 'models')}")

    print(f"\n What was generated:")
    print(f"   - UESGraph JSON file with network topology and attributes")
    print(f"   - Modelica simulation model in timestamped directory")

    print(f"\n Next Steps:")
    print(f"   Run the simulation to analyze district heating performance")

    print("\n" + "="*80)




if __name__ == "__main__":
    print("\n" + "="*80)
    print("UESGraphs Example 16: Complete GeoJSON to Modelica Workflow")
    print("Using the new Excel-based parameter configuration system")
    print("="*80)

    main()

    # Show optional features
    demo_alternative_usage()
    demo_simplification()

    print("\n" + "="*80)
    print("Example script completed. Check your workspace for outputs!")
    print("="*80 + "\n")
