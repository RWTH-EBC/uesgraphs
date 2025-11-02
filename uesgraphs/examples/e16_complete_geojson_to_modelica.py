"""
Complete Workflow: GeoJSON Import to Modelica Code Generation
==============================================================

This example demonstrates the complete workflow for converting a district heating network
from GeoJSON format to executable Modelica simulation models using the new Excel-based
parameter configuration system.

Workflow Overview:
-----------------
1. **GeoJSON Import**: Load network topology, buildings, and supply stations from GeoJSON files
2. **Demand Data Assignment**: Attach heating, DHW, and cooling demand time series to buildings
3. **Excel-Based Configuration**: Use Excel template to configure all simulation and component parameters
4. **Modelica Generation**: Automatically generate ready-to-simulate Modelica code

Key Features of the New Pipeline:
---------------------------------
- **Excel-Based Configuration**: All parameters (simulation settings, pipe properties, supply/demand
  parameters) are configured in a single Excel file (uesgraphs_parameters_template.xlsx)

- **Flexible Parameter Sources**: Parameters can be specified in three ways:
  * Graph attributes (from GeoJSON or set programmatically)
  * Excel template (for uniform values across all components)
  * References (Excel values starting with @ reference graph attributes)

- **Template Selection**: Choose Modelica component templates via Excel:
  * Standard templates: Specify template name (e.g., 'AixLib_Fluid_...')
  * Custom templates: Provide absolute path to .mako template file

- **Validation**: Automatic checking of required (MAIN) vs optional (AUX) parameters
  * MAIN parameters: Must be provided (error if missing)
  * AUX parameters: Optional (Modelica defaults used if not provided)

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
├── visualizations/                     # Network topology visualizations
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
    """
    Main execution function demonstrating the complete workflow.
    """
    print("="*80)
    print("E16: Complete Workflow - GeoJSON to Modelica Code Generation")
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
    print("\n🗺️  STEP 2: Importing district network from GeoJSON files...")
    print("   This step creates a graph structure from geographic data:")
    print("   - Network topology (pipes) from network.geojson")
    print("   - Building locations and attributes from buildings.geojson")
    print("   - Supply station from supply.geojson")

    graph = UESGraph()
    graph.from_geojson(
        network_path=network_geojson,
        buildings_path=buildings_geojson,
        supply_path=supply_geojson,
        name='simple_district',
        save_path=workspace,
        generate_visualizations=True
    )

    # Display network statistics
    print(f"\n   ✓ GeoJSON import successful!")
    print(f"     - Buildings: {len(graph.nodelist_building)}")
    print(f"     - Network edges (pipes): {graph.number_of_edges()}")
    print(f"     - Total pipe length: {graph.calc_network_length(network_type='heating'):.2f} m")

    # Save the imported graph
    graph_json_path = os.path.join(workspace, 'simple_district_graph.json')
    graph.to_json(path=workspace, name='simple_district_graph', all_data=True, prettyprint=True)
    print(f"     - Saved graph to: {graph_json_path}")
    print(f"     - Visualizations: {os.path.join(workspace, 'visualizations')}")

    # =========================================================================
    # STEP 3: Generate Modelica Code using New Excel-Based Pipeline
    # =========================================================================
    print("\n⚙️  STEP 3: Generating Modelica code using Excel-based pipeline...")
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

    print("\n   🚀 Starting pipeline (this may take a few moments)...\n")

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

        print("\n   ✅ SUCCESS: Modelica code generation completed!")

    except Exception as e:
        print(f"\n   ❌ ERROR: Pipeline failed with: {e}")
        print("   💡 Check the log file for detailed error information")
        raise

    # =========================================================================
    # STEP 4: Summary and Next Steps
    # =========================================================================
    print("\n" + "="*80)
    print("🎉 E16 Example Completed Successfully!")
    print("="*80)

    print(f"\n📂 Output Locations:")
    print(f"   Workspace: {workspace}")
    print(f"   Generated Models: {os.path.join(workspace, 'models')}")
    print(f"   Visualizations: {os.path.join(workspace, 'visualizations')}")

    print(f"\n📊 What was generated:")
    print(f"   - UESGraph JSON file with network topology and attributes")
    print(f"   - Network visualization plots (if matplotlib available)")
    print(f"   - Modelica simulation model in timestamped directory")
    print(f"   - Component models for pipes, supply, and demand substations")

    print(f"\n🔧 Next Steps:")
    print(f"   1. Review the generated Modelica files in the 'models' directory")
    print(f"   2. Open the main .mo file in Dymola or OpenModelica")
    print(f"   3. Ensure AixLib library is loaded in your simulation environment")
    print(f"   4. Run the simulation to analyze district heating performance")

    print(f"\n💡 Tips:")
    print(f"   - Modify Excel template to test different configurations")
    print(f"   - Adjust simplification_level parameter for larger networks")
    print(f"   - Change log_level to logging.DEBUG for detailed diagnostics")
    print(f"   - Use custom templates by specifying template_path in Excel")

    print("\n" + "="*80)


def demo_alternative_usage():
    """
    Optional: Demonstrates alternative ways to use the pipeline.
    """
    print("\n💡 Alternative Usage Examples:")
    print("\n   1️⃣  Direct from GeoJSON (current example):")
    print("   ────────────────────────────────────────")
    print("   graph = UESGraph()")
    print("   graph.from_geojson(...)")
    print("   uesgraph_to_modelica(uesgraph=graph, ...)")
    print("   → Edge names are automatically generated if missing")

    print("\n   2️⃣  From saved JSON file:")
    print("   ────────────────────────")
    print("   # First save the graph")
    print("   graph.to_json(path='workspace', name='my_network')")
    print("   ")
    print("   # Later, load directly in pipeline")
    print("   uesgraph_to_modelica(")
    print("       uesgraph='workspace/my_network.json',  # ← Path as string!")
    print("       ...)")
    print("   → No need to load graph first, pipeline does it automatically")

    print("\n   3️⃣  With network simplification:")
    print("   ────────────────────────────────")
    print("   uesgraph_to_modelica(")
    print("       uesgraph=graph,")
    print("       simplification_level=1,  # 0=none, 1=medium, 2=aggressive")
    print("       ...)")
    print("   → Reduces pipe segments for faster simulation")


def demo_simplification():
    """
    Optional: Demonstrates network simplification feature.

    Network simplification reduces the number of pipe segments by removing
    unnecessary nodes while preserving the overall topology. This is useful
    for large networks to reduce simulation time.

    Simplification levels:
    - 0: No simplification (full network)
    - 1: Remove simple pass-through nodes
    - 2: Aggressive simplification (merge short segments)
    """
    print("\n📐 Network Simplification Example:")
    print("   To use simplification, change the simplification_level parameter:")
    print("   ")
    print("   uesgraph_to_modelica(")
    print("       uesgraph=graph,")
    print("       simplification_level=1,  # Try 1 or 2 for simplification")
    print("       ...")
    print("   )")
    print("   ")
    print("   Higher values = more aggressive simplification")
    print("   Trade-off: Faster simulation vs. geometric accuracy")


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
