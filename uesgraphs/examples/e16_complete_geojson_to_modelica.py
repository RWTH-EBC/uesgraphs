"""
Example 16: GeoJSON to Modelica Code Generation
================================================

Demonstrates the complete workflow for converting a district heating network from
GeoJSON format to executable Modelica simulation models using the Excel-based
parameter configuration system.

Workflow:
---------
1. Import network topology from GeoJSON files (pipes, buildings, supply station)
2. Configure parameters via Excel template (uesgraphs_parameters_template.xlsx)
3. Generate Modelica code with automatic parameter assignment and validation

Key Features:
-------------
- Excel-based configuration: All parameters in one file (Simulation, Pipes, Supply, Demands sheets)
- Template selection: Choose Modelica component templates via Excel
- Parameter sources: Graph attributes, Excel values, or @references to graph data
- Automatic validation: Required (MAIN) vs optional (AUX) parameter checking
- Connector handling: Automatic time-series conversion for model inputs

Excel Template Structure:
-------------------------
The template (uesgraphs_parameters_template.xlsx) contains parameter definitions where:
- MAIN parameters: Required (error if missing)
- AUX parameters: Optional (Modelica defaults used if not provided)
- @references: Excel values starting with @ reference graph attributes (e.g., @diameter)
- Connectors: Template variables marked in get_connector_names() that require time-series input

Template-Excel Interaction:
----------------------------
1. Templates define required parameters via get_main_parameters() and get_aux_parameters()
2. Excel provides uniform values for all components of the same type
3. Graph attributes override Excel values (never overwritten by Excel)
4. Pipeline validates that all MAIN parameters are available
5. Missing AUX parameters trigger warnings but don't stop generation

Input Requirements:
-------------------
- Network GeoJSON: LineString features (pipe network)
- Buildings GeoJSON: Point/Polygon features (demand buildings)
- Supply GeoJSON: Point features with is_supply_heating=True
- Demand CSVs: Time series for heating, DHW, cooling (8760 hourly values)
- Ground temperature CSV: Temperature profiles at various depths
- Excel config: uesgraphs_parameters_template.xlsx
"""

import os
import sys
import logging

# Add parent directory to path for local development
script_dir = os.path.dirname(os.path.abspath(__file__))
uesgraphs_root = os.path.dirname(os.path.dirname(script_dir))
if uesgraphs_root not in sys.path:
    sys.path.insert(0, uesgraphs_root)

from uesgraphs import UESGraph
from uesgraphs.systemmodels.model_generation_pipeline import uesgraph_to_modelica


def workspace_example(name_workspace):
    """Create and return workspace directory."""
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
    """Execute the complete GeoJSON to Modelica workflow."""

    # Setup workspace and file paths
    workspace = workspace_example("e16")

    uesgraphs_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(uesgraphs_dir, 'uesgraphs', 'data', 'examples')
    geojson_dir = os.path.join(data_dir, 'e15_geojson')

    network_geojson = os.path.join(geojson_dir, 'network.geojson')
    buildings_geojson = os.path.join(geojson_dir, 'buildings.geojson')
    supply_geojson = os.path.join(geojson_dir, 'supply.geojson')

    input_heating = os.path.join(data_dir, 'demands-heat.csv')
    input_dhw = os.path.join(data_dir, 'demands-dhw.csv')
    input_cooling = os.path.join(data_dir, 'demands-cool.csv')
    ground_temp_path = os.path.join(data_dir, 'ground_temps_hassel.csv')

    excel_config_path = os.path.join(uesgraphs_dir, 'uesgraphs', 'data',
                                     'uesgraphs_parameters_template.xlsx')

    # Import district network from GeoJSON
    print("Importing network from GeoJSON...")
    graph = UESGraph()
    graph.from_geojson(
        network_path=network_geojson,
        buildings_path=buildings_geojson,
        supply_path=supply_geojson,
        name='simple_district',
        save_path=workspace,
        generate_visualizations=True
    )

    print(f"Network imported: {len(graph.nodelist_building)} buildings, "
          f"{graph.number_of_edges()} pipes, "
          f"{graph.calc_network_length(network_type='heating'):.1f}m total length")

    # Save graph for inspection
    graph.to_json(path=workspace, name='simple_district_graph', all_data=True, prettyprint=True)

    # Generate Modelica code using Excel-based pipeline
    print("\nGenerating Modelica code...")
    print(f"Using Excel config: {os.path.basename(excel_config_path)}")

    try:
        uesgraph_to_modelica(
            uesgraph=graph,
            simplification_level=0,
            workspace=workspace,
            sim_setup_path=excel_config_path,
            input_heating=input_heating,
            input_dhw=input_dhw,
            input_cooling=input_cooling,
            ground_temp_path=ground_temp_path,
            log_level=logging.INFO
        )
        print("\nModelica generation completed successfully")
        print(f"Output location: {os.path.join(workspace, 'models')}")

    except Exception as e:
        print(f"\nError during code generation: {e}")
        print("Check log file for details")
        raise


def demo_alternative_usage():
    """Show alternative ways to use the pipeline."""
    print("\n" + "="*80)
    print("Alternative Usage Patterns:")
    print("="*80)

    print("\n1. Load from saved JSON:")
    print("   uesgraph_to_modelica(")
    print("       uesgraph='workspace/my_network.json',  # String path instead of object")
    print("       ...)")

    print("\n2. Network simplification:")
    print("   uesgraph_to_modelica(")
    print("       uesgraph=graph,")
    print("       simplification_level=1,  # 0=none, 1=medium, 2=aggressive")
    print("       ...)")

    print("\n3. Custom templates:")
    print("   - Modify 'template' field in Excel Pipes/Supply/Demands sheets")
    print("   - Use template_path for absolute paths to custom .mako files")

    print("\n4. Parameter priority (highest to lowest):")
    print("   - Graph attributes (from GeoJSON or programmatically set)")
    print("   - Excel template values")
    print("   - Modelica defaults (for optional AUX parameters)")


if __name__ == "__main__":
    print("="*80)
    print("E16: GeoJSON to Modelica Code Generation")
    print("="*80)

    main()
    demo_alternative_usage()

    print("\n" + "="*80)
