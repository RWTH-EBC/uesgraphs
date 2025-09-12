"""
Template-Based Modelica Model Generation for District Heating Networks (Advanced)
================================================================================

This example demonstrates the advanced workflow for generating Modelica models from UESGraphs,
with emphasis on the critical relationship between Modelica templates and parameter dictionaries.

Educational Focus: Template-Parameter Correlation
===============================================

The core principle of template-based model generation is that **templates determine parameters**.
This example teaches this fundamental concept through a complete workflow:

1. **Template Selection**: Choose Modelica component templates for supply, demand, and pipes
2. **Parameter Analysis**: Understand what parameters each template requires
3. **Parameter Dictionary**: Create a dictionary with template-compliant parameter names
4. **Demand Data Integration**: Load and assign demand data to buildings
5. **Template Validation**: Validate that all template requirements are satisfied
6. **Model Generation**: Generate complete Modelica simulation package

Template-Parameter Workflow
==========================

Step 1: Choose Templates
------------------------
Select appropriate Modelica templates based on your modeling requirements:

Supply Template: AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal
  → Requires: TIn (inlet temperature), dpIn (pressure), pReturn (return pressure)

Demand Template: AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp  
  → Requires: Q_flow_nominal, dTDesign, TReturn, dp_nominal

Pipe Template: AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded
  → Requires: dIns, kIns, length, m_flow_nominal, roughness

Step 2: Create Parameter Dictionary
----------------------------------
Based on template requirements, create a parameter dictionary with:
- Design parameters (temperatures, pressures, flows)
- Physical parameters (insulation, roughness, sizing)  
- Component parameters (pressure drops, temperature differences)

Step 3: Demand Data Integration
------------------------------
Real networks require actual demand profiles:
- Load heating/cooling/DHW demands from CSV files
- Assign demands to building nodes with intelligent fallbacks
- Calculate peak loads for component sizing

Step 4: Template Validation & Assignment
---------------------------------------
Ensure parameter compatibility:
- Validate all required template parameters are present
- Map design parameters to template-specific parameter names
- Assign calculated values (like Q_flow_nominal from demand data)

Step 5: Modelica Model Generation
--------------------------------
Generate complete simulation package:
- Component definitions with template-specific parameters
- Network connections and topology
- Simulation settings and solver configuration
- Ready-to-run Modelica package

Network Example: Seestadt District Heating
==========================================

This example uses the Seestadt network (Vienna, Austria) to demonstrate:
- Real network topology with 5 buildings and 1 supply node
- Actual demand profiles for heating, cooling, and DHW
- Template-based model generation with parameter validation
- Complete Modelica simulation package ready for Dymola

Key Learning Outcomes
====================

After running this example, you will understand:
1. How template selection drives parameter requirements
2. The importance of exact parameter naming for template compatibility  
3. How to validate template-parameter relationships
4. Integration of real demand data with template-based modeling
5. Complete workflow from UESGraph to executable Modelica simulation

Functions:
---------
main():
    Complete demonstration workflow with Seestadt network

model_generation_seestadt(dir_dest):
    Generate Modelica model for Seestadt network with full template validation

validate_template_parameters(params_dict, template_models):
    Educational validation of template-parameter compatibility

setup_supply_demand_parameters(uesgraph, params_dict, template_models):
    Template-specific parameter assignment for supply and demand nodes

assign_demand_data(uesgraph, input_paths_dict):
    Load and assign real demand profiles from CSV files

Requirements:
------------
- uesgraphs with systemmodels module
- Seestadt UESGraph JSON file (included in data/examples/)
- Demand CSV files (heating, cooling, DHW) in data/examples/
- AixLib 2.1.0 for Modelica simulation (not required for model generation)

Usage:
------
Run this script to generate a complete Modelica simulation package:
    python -m uesgraphs.examples.e13_model_generationII_example

The generated model will be saved in the workspace under e13/Seestadt/model/
"""

import os
from pathlib import Path
import datetime
import uesgraphs.systemmodels.utilities as sysut
from uesgraphs.uesgraph import UESGraph
import uesgraphs.utilities as ut
import pandas as pd


def main():
    """
    Main demonstration function showing complete template-based modeling workflow
    
    This function demonstrates the educational workflow from template selection
    to complete Modelica model generation using the Seestadt district heating network.
    """
    start_time = datetime.datetime.now()
    
    print("=" * 80)
    print("Template-Based Modelica Model Generation - Advanced Example (e13)")
    print("=" * 80)
    print("Educational Focus: Template-Parameter Correlation in Model Generation")
    print()
    
    # Create workspace directory structure (following e11 pattern)
    workspace = ut.make_workspace("uesmodel_examples") 
    from uesgraphs.examples import e1_readme_example as e1
    workspace = e1.workspace_example("e13")
    
    # Create Seestadt-specific workspace
    seestadt_workspace = os.path.join(workspace, "Seestadt")
    
    # Create directory structure for model files and results
    dir_input, dir_model, dir_result, dir_visualization = create_dirs(seestadt_workspace)
    
    print(f"Workspace created at: {seestadt_workspace}")
    print(f"Model files will be saved to: {dir_model}")
    print()
    
    # Generate Seestadt Modelica model with complete template workflow
    print("Starting template-based model generation for Seestadt network...")
    print()
    
    try:
        model = model_generation_seestadt(dir_model)
        if model:
            print("✓ Model generation completed successfully!")
            print(f"✓ Modelica package saved to: {dir_model}")
            print(f"✓ System model graph exported to: {dir_model}/sysmmodel_graph.json")
        else:
            print("✗ Model generation failed!")
            
    except Exception as e:
        print(f"✗ Error in model generation: {e}")
        import traceback
        traceback.print_exc()
    
    # Calculate and display runtime
    end_time = datetime.datetime.now()
    runtime = end_time - start_time
    
    print()
    print("=" * 80)
    print(f"Example e13 completed in {runtime}")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Open the generated Modelica package in Dymola")
    print("2. Simulate the Seestadt_heating_network model")
    print("3. Analyze results and modify parameters as needed")
    print("4. Experiment with different templates and parameter combinations")


def create_dirs(dir_project):
    """
    Create standardized directory structure for model files and results
    
    Following the e11 example pattern for consistency.
    
    Parameters
    ----------
    dir_project : str
        Base directory of the project where directories will be created
        
    Returns
    -------
    tuple
        (dir_input, dir_model, dir_result, dir_visualization) directory paths
    """
    if not os.path.exists(dir_project):
        os.makedirs(dir_project)
    
    directories = {
        'input': os.path.join(dir_project, "input"),
        'model': os.path.join(dir_project, "model"), 
        'result': os.path.join(dir_project, "result"),
        'visualization': os.path.join(dir_project, "visualization")
    }
    
    # Create all directories
    for dir_name, dir_path in directories.items():
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    # Create design subdirectory in input
    design_dir = os.path.join(directories['input'], "design")
    if not os.path.exists(design_dir):
        os.makedirs(design_dir)
    
    return directories['input'], directories['model'], directories['result'], directories['visualization']


def load_seestadt_uesgraph():
    """
    Load the Seestadt UESGraph from JSON file
    
    Returns
    -------
    UESGraph or None
        The loaded UESGraph object, or None if loading failed
    """
    try:
        # Get the path to the JSON file
        current_dir = Path(__file__).parent
        json_path = current_dir.parent / "data" / "examples" / "transurban_seestadt_uesgraphs.json"
        
        print(f"Loading Seestadt UESGraph from: {json_path}")
        
        if not json_path.exists():
            print(f"✗ JSON file not found: {json_path}")
            return None
            
        # Create UESGraph instance and load from JSON
        uesgraph = UESGraph()
        uesgraph.from_json(path=str(json_path), network_type="heating")
        
        # Ensure network type is set
        uesgraph.graph["network_type"] = "heating"
        uesgraph.graph["name"] = "seestadt"

        print(f"✓ Loaded network with {len(uesgraph.nodes())} nodes and {len(uesgraph.edges())} edges")
        return uesgraph
        
    except Exception as e:
        print(f"✗ Error loading UESGraph: {e}")
        return None


def combine_heating_dhw(heat_demand, dhw_demand):
    """
    Combines heating and DHW demands where both are non-zero for peak load calculation.
    """
    heating_combined = []
    dhw_adjusted = []
    
    for heat_val, dhw_val in zip(heat_demand, dhw_demand):
        if heat_val != 0.0 and dhw_val != 0.0:
            heating_combined.append(heat_val + dhw_val)
            dhw_adjusted.append(0.0)
        else:
            heating_combined.append(heat_val)
            dhw_adjusted.append(dhw_val)
            
    return heating_combined, dhw_adjusted


def assign_demand_data(uesgraph, input_paths_dict, input_types=["heating", "cooling", "dhw"], demand_mode=0):
    """
    Assigns energy demand data to buildings in a UES (Urban Energy Systems) graph.
    
    This function reads demand profiles from CSV files and assigns them to building nodes
    in the graph. For buildings without specific demand data, it uses a fallback profile
    (dummy demand) based on the first building in the respective CSV file.

    Parameters
    ----------
    uesgraph : uesgraphs Graph
        The urban energy system graph containing building nodes.
    input_paths_dict : dict
        Dictionary containing file paths for each demand type.
        Expected keys: 'heating', 'cooling', 'dhw'.
    input_types : list, optional
        List of demand types to process. Default is ["heating", "cooling", "dhw"].
    demand_mode : int, optional
        Mode for demand calculation. Currently only mode 0 is implemented,
        which combines heating and DHW demands for peak load calculation.

    Returns
    -------
    tuple
        - Updated UES graph with demand data assigned to building nodes
        - Message string containing information about the data assignment process
    """
    msg = "Demand data assignment results:\n"

    # Define empty dictionaries for demand data
    dict_inputs = {}
    dummy_demand = {}

    try:
        for input_type in input_types:
            df = pd.read_csv(input_paths_dict[input_type],
                            parse_dates=True,
                            index_col=0)
            dict_inputs[input_type] = df.rename(columns=lambda x: x.lower())
            
            # Store dummy demand (first data column) for missing buildings
            dummy_demand[input_type] = df[df.columns[0]].tolist()
            print(f"  ✓ Loaded {input_type} data: {len(df)} time steps, {len(df.columns)} buildings")
    except FileNotFoundError as e:
        print(f"✗ Failed to load demand data: {e}")
        return uesgraph, f"Error: {e}"

    missing_bldgs = dict_inputs["heating"].columns.to_list()

    # Process each building
    for bldg_node in uesgraph.nodelist_building:
        if uesgraph.nodes[bldg_node].get("is_supply_heating", False):
            continue

        bldg_name = str(uesgraph.nodes[bldg_node]["name"]).lower()
        demands = {}

        # Get demand profiles for each type, use dummy if missing
        for input_type in input_types:
            try:
                demands[input_type] = dict_inputs[input_type][bldg_name].tolist()
                if input_type == "heating" and bldg_name in missing_bldgs:
                    missing_bldgs.remove(bldg_name)
            except KeyError:
                demands[input_type] = dummy_demand[input_type]
                msg += f"  - Building {bldg_name}: using dummy {input_type} demand\n"
        
        # Combine heating and DHW demands where both are non-zero
        if demand_mode == 0:
            heating_combined, dhw_adjusted = combine_heating_dhw(demands["heating"], demands["dhw"])

        # Save demands to node
        node = uesgraph.nodes[bldg_node]
        node.update({
            "input_dhw": demands["dhw"],
            "input_heat": demands["heating"],
            "input_cool": demands["cooling"],
            "heatDemand_max": max(max(heating_combined), max(dhw_adjusted)),
            "coldDemand_max": max(demands["cooling"])
        })
        
    if len(missing_bldgs) > 0:
        msg += f"Buildings not found in CSV: {missing_bldgs}\n"
    else:
        msg += "All buildings successfully matched with demand data.\n"

    return uesgraph, msg


def validate_template_parameters(params_dict, template_models):
    """
    Educational function: Validate that parameter dictionary contains all required 
    parameters for the specified Modelica templates.
    
    This function demonstrates the fundamental principle that each Modelica template
    has specific parameter requirements that MUST be satisfied for successful compilation.
    Understanding these requirements is crucial for template-based model generation.
    
    Template Parameter Requirements:
    ===============================
    
    Supply Template (SourceIdeal):
    - TIn: Supply temperature [K] 
    - dpIn: Supply pressure [Pa] (as list!)
    - pReturn: Return pressure [Pa]
    
    Demand Template (VarTSupplyDp):  
    - Q_flow_nominal: Nominal heat flow [W]
    - dTDesign: Design temperature difference [K]
    - TReturn: Return temperature [K]
    - dp_nominal: Nominal pressure drop [Pa]
    
    Pipe Template (PlugFlowPipeEmbedded):
    - dIns: Insulation diameter [m] 
    - kIns: Insulation thermal conductivity [W/(m·K)]
    - length: Pipe length [m] (from graph)
    - m_flow_nominal: Nominal mass flow [kg/s]
    """
    print("\n" + "=" * 60)
    print("EDUCATIONAL: Template Parameter Validation")
    print("=" * 60)
    print("Each Modelica template requires specific parameters with exact names.")
    print("This validation ensures our parameter dictionary matches template needs.")
    print()
    
    # Define required parameters for each template type
    template_requirements = {
        'supply': {
            'required_params': ['T_supply', 'p_supply', 'p_return'],
            'template_mapping': {
                'T_supply': 'TIn',
                'p_supply': 'dpIn', 
                'p_return': 'pReturn'
            },
            'description': 'Supply template needs inlet temperature and pressures'
        },
        'demand': {
            'required_params': ['dT_design', 'T_return', 'dp_nominal'],
            'template_mapping': {
                'dT_design': 'dTDesign',
                'T_return': 'TReturn',
                'dp_nominal': 'dp_nominal'
            },
            'description': 'Demand template needs temperature differences and pressure drops'
        },
        'pipe': {
            'required_params': ['dIns', 'kIns', 'm_flow_nominal'],
            'template_mapping': {
                'dIns': 'dIns',
                'kIns': 'kIns', 
                'm_flow_nominal': 'm_flow_nominal'
            },
            'description': 'Pipe template needs insulation and flow parameters'
        }
    }
    
    # Validate each template's requirements
    all_valid = True
    for template_type, requirements in template_requirements.items():
        template_name = template_models.get(template_type, 'Unknown')
        print(f"Template: {template_name}")
        print(f"Purpose: {requirements['description']}")
        
        missing_params = []
        for param in requirements['required_params']:
            if param not in params_dict:
                missing_params.append(param)
                all_valid = False
            else:
                template_param = requirements['template_mapping'][param]
                value = params_dict[param]
                print(f"  ✓ {param} → {template_param} = {value}")
        
        if missing_params:
            print(f"  ✗ Missing required parameters: {missing_params}")
        print()
    
    if not all_valid:
        raise ValueError("Template parameter validation failed. Please check missing parameters above.")
    
    print("✓ All template parameter requirements satisfied!")
    print("This ensures successful Modelica template rendering.")
    print("=" * 60)


def setup_supply_demand_parameters(uesgraph, params_dict, template_models):
    """
    Educational function: Setup supply and demand node parameters with template-specific naming.
    
    This function demonstrates how parameter names in uesgraphs must match exactly 
    what the Modelica templates expect. This is the core principle of template-based 
    model generation.
    
    Key Learning: Template Parameter Mapping
    =======================================
    
    Our Design Parameters → Template Parameter Names:
    - T_supply → TIn (supply inlet temperature)
    - p_supply → dpIn (supply pressure as list!) 
    - p_return → pReturn (return pressure)
    - dT_design → dTDesign (design temperature difference)
    - T_return → TReturn (return temperature) 
    
    The exact naming comes from analyzing the .mako template files!
    """
    print("\n" + "=" * 60)
    print("EDUCATIONAL: Template-Specific Parameter Assignment")
    print("=" * 60)
    print("Assigning parameters with names that match Modelica template expectations.")
    print()
    
    for node in uesgraph.nodelist_building:
        node_data = uesgraph.nodes[node]
        node_name = node_data.get('name', node)
        
        if node_data.get('is_supply_heating', False):
            # Supply nodes: Use SourceIdeal template parameter names
            print(f"Supply node '{node_name}':")
            print(f"  - TIn (inlet temp) = {params_dict['T_supply']:.1f} K ({params_dict['T_supply']-273.15:.1f}°C)")
            print(f"  - dpIn (pressure) = [{params_dict['p_supply']:,.0f}] Pa (as list!)")  
            print(f"  - pReturn (return) = {params_dict['p_return']:,.0f} Pa")
            
            node_data.update({
                'TIn': params_dict['T_supply'],           # Template requires 'TIn'
                'dpIn': [params_dict['p_supply']],        # Template requires 'dpIn' as LIST!
                'pReturn': params_dict['p_return'],       # Template requires 'pReturn'
            })
        else:
            # Demand nodes: Use VarTSupplyDp template parameter names  
            # Calculate Q_flow_nominal from assigned demand data
            heat_demand = node_data.get('input_heat', [0])
            dhw_demand = node_data.get('input_dhw', [0])
            cool_demand = node_data.get('input_cool', [0])
            
            q_flow_nominal = max(
                max(heat_demand) if heat_demand else 0,
                max(dhw_demand) if dhw_demand else 0, 
                max(cool_demand) if cool_demand else 0
            )
            
            print(f"Demand node '{node_name}':")
            print(f"  - Q_flow_nominal = {q_flow_nominal:,.0f} W (calculated from demand data)")
            print(f"  - dTDesign = {params_dict['dT_design']} K")
            print(f"  - TReturn = {params_dict['T_return']:.1f} K ({params_dict['T_return']-273.15:.1f}°C)")
            
            node_data.update({
                'Q_flow_nominal': q_flow_nominal,         # Template requires 'Q_flow_nominal' 
                'dTDesign': params_dict['dT_design'],     # Template requires 'dTDesign'
                'TReturn': params_dict['T_return'],       # Template requires 'TReturn'
            })
        
        # All buildings get return temperature (used by templates)
        node_data['TReturn'] = params_dict['T_return']
        print()
    
    print("✓ All nodes configured with template-specific parameter names!")
    print("=" * 60)
    return uesgraph


def setup_edge_mass_flow(uesgraph, params_dict):
    """
    Educational function: Setup mass flow parameters for pipe edges.
    
    All pipe templates require 'm_flow_nominal' for proper sizing and simulation.
    In a real application, this would be calculated based on demand distribution,
    but for this example we use a simplified approach.
    """
    print("\n" + "=" * 60)
    print("EDUCATIONAL: Edge Mass Flow Assignment")
    print("=" * 60)
    print("All pipe templates require 'm_flow_nominal' for hydraulic calculations.")
    print()
    
    m_flow = params_dict['m_flow_nominal'] 
    edge_count = 0
    
    for edge in uesgraph.edges():
        uesgraph.edges[edge]['m_flow_nominal'] = m_flow
        edge_count += 1
    
    print(f"Set m_flow_nominal = {m_flow} kg/s for {edge_count} pipe edges")
    print("Note: Real applications would calculate this from demand distribution!")
    print("=" * 60)
    
    return uesgraph


def setup_building_parameters(uesgraph, params_dict):
    """
    Configure building parameters based on type (supply or demand).
    
    Note: This function could be moved to uesgraphs core in the future
    as part of a general component configuration system.
    """
    
    # Common parameters for all buildings
    common_params = {
        'allowFlowReversal': params_dict['allowFlowReversal']
    }
    
    # Specific parameters for demand buildings
    demand_params = {
        'dp_nominal': params_dict['dp_nominal'],
        'dT_Network': params_dict['dT_Network'],
        'T_dhw_supply': params_dict['T_dhw_supply'],
        'T_heat_supply': params_dict['T_heat_supply'],
        'T_cold_supply': params_dict['T_cold_supply'],
    }
    
    # Specific parameters for supply buildings
    supply_params = {
        'heatDemand_max_supply': params_dict['heatDemand_max_supply'], 
        'dT_Network': params_dict['dT_Network'],
        'T_dhw_supply': params_dict['T_dhw_supply'],
        'T_heat_supply': params_dict['T_heat_supply'],
        'T_cold_supply': params_dict['T_cold_supply'],
    }
    
    # Update all nodes
    for node in uesgraph.nodelist_building:
        node_data = uesgraph.nodes[node]
        
        # Update common parameters first
        node_data.update(common_params)
        
        if not node_data.get('is_supply_heating', False):
            # Demand building
            node_data.update(demand_params)
        else:
            # Supply building
            node_data.update(supply_params)
    return uesgraph


def setup_pipe_parameters(uesgraph, params_dict):
    """
    Configure pipe parameters for all edges in the network graph.
    
    Note: This function could be moved to uesgraphs core in the future
    as part of a general component configuration system.
    
    Args:
        uesgraph: uesgraphs graph containing the network structure
        params_dict: dictionary containing configuration parameters
    """
    pipe_params = {
        'dIns': params_dict['dIns'],                    # Insulation diameter
        'kIns': params_dict['kIns'],                    # Insulation thermal conductivity
        'fac': params_dict['fac'],                      # Scaling factor
        'roughness': params_dict['roughness'],          # Pipe roughness
        'allowFlowReversal': params_dict['allowFlowReversal'],
    }
    
    # Update pipe parameters for each edge
    for edge in uesgraph.edges():
        # Copy base parameters
        uesgraph.edges[edge].update(pipe_params)
        # Set hydraulic diameter based on edge-specific inner diameter
        uesgraph.edges[edge]['dh'] = uesgraph.edges[edge].get('diameter', 0.05)

    return uesgraph


def model_generation_seestadt(dir_dest):
    """
    Generate Modelica model for Seestadt network with complete template-based workflow
    
    This function demonstrates the complete educational workflow:
    1. Template selection and requirements analysis
    2. Parameter dictionary creation and validation  
    3. Demand data integration from CSV files
    4. Template-specific parameter assignment
    5. Modelica model generation
    
    Parameters
    ----------
    dir_dest : str
        Directory to store generated Modelica models
        
    Returns
    -------
    SystemModelHeating or None
        Generated system model object, or None if generation failed
    """
    print("=" * 80)
    print("SEESTADT TEMPLATE-BASED MODEL GENERATION")
    print("=" * 80)
    
    # Step 1: Load the Seestadt UESGraph 
    graph = load_seestadt_uesgraph()
    if not graph:
        print("✗ Failed to load UESGraph, cannot proceed")
        return None
    
    print(f"✓ UESGraph loaded successfully")
    print(f"  - Network: {len(graph.nodes())} nodes, {len(graph.edges())} edges")
    print(f"  - Buildings: {len(graph.nodelist_building)} total")
    print()
    
    # Step 2: Load and assign demand data from CSV files
    print("Step 1: Loading Real Demand Data")
    print("-" * 40)
    current_dir = Path(__file__).parent
    data_dir = current_dir.parent / "data" / "examples"
    
    input_paths_dict = {
        "heating": str(data_dir / "demands-heat.csv"),
        "cooling": str(data_dir / "demands-cool.csv"),
        "dhw": str(data_dir / "demands-dhw.csv")
    }
    
    try:
        graph, demand_msg = assign_demand_data(graph, input_paths_dict)
        print("✓ Demand data assigned successfully")
        print(demand_msg)
    except Exception as e:
        print(f"✗ Error assigning demand data: {e}")
        return None
    
    # Step 3: Define templates and create parameter dictionary
    print("Step 2: Template Selection & Parameter Dictionary")
    print("-" * 50)
    
    # Define template models being used (this drives everything!)
    template_models = {
        'supply': "AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        'demand': "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
        'pipe': "AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded"
    }
    
    print("Selected Modelica Templates:")
    for template_type, template_name in template_models.items():
        print(f"  {template_type.capitalize()}: {template_name}")
    print()
    
    # Define comprehensive parameter dictionary based on template requirements
    params_dict = {
        # Thermal/Hydraulic Design Parameters (for templates)
        'T_supply': 273.15 + 80,        # 80°C supply temperature [K] 
        'T_return': 273.15 + 50,        # 50°C return temperature [K]
        'p_supply': 6e5,                # 6 bar supply pressure [Pa]
        'p_return': 2e5,                # 2 bar return pressure [Pa]
        'dT_design': 30,                # 30K design temperature difference [K]
        'm_flow_nominal': 1.0,          # 1 kg/s nominal mass flow [kg/s]
        
        # Physical Pipe Parameters (for pipe templates)
        'dIns': 0.05,                   # 50mm insulation diameter [m]
        'kIns': 0.04,                   # Insulation thermal conductivity [W/(m·K)]
        'fac': 1.0,                     # Scaling factor [-]
        'roughness': 0.0001,            # Pipe roughness [m]
        'allowFlowReversal': True,      # Allow flow reversal [bool]
        
        # Building Component Parameters (for supply/demand templates)
        'dp_nominal': 50000,            # 50 kPa nominal pressure drop [Pa]
        'dT_Network': 30,               # 30K network temperature difference [K]
        'T_dhw_supply': 273.15 + 60,    # 60°C DHW supply temperature [K]
        'T_heat_supply': 273.15 + 80,   # 80°C heating supply temperature [K]
        'T_cold_supply': 273.15 + 10,   # 10°C cooling supply temperature [K]
        'heatDemand_max_supply': 100000, # 100kW max supply capacity [W]
    }
    
    print("Parameter Dictionary Created:")
    print(f"  Thermal parameters: T_supply={params_dict['T_supply']-273.15:.1f}°C, T_return={params_dict['T_return']-273.15:.1f}°C")
    print(f"  Pressure parameters: p_supply={params_dict['p_supply']/1e5:.1f} bar, p_return={params_dict['p_return']/1e5:.1f} bar")
    print(f"  Physical parameters: dIns={params_dict['dIns']*1000:.0f}mm, kIns={params_dict['kIns']:.3f} W/(m·K)")
    print()
    
    # Step 4: Setup network component parameters
    try:
        # Setup pipe parameters
        graph = setup_pipe_parameters(graph, params_dict)
        print("✓ Pipe parameters configured")
        
        # Setup building parameters  
        graph = setup_building_parameters(graph, params_dict)
        print("✓ Building parameters configured")
        
    except Exception as e:
        print(f"✗ Error setting up component parameters: {e}")
        return None
    
    # Step 5: Template-specific parameter validation and assignment
    print("\nStep 3: Template Parameter Validation & Assignment")  
    print("-" * 52)
    
    try:
        # Validate that our parameter dictionary matches template requirements
        validate_template_parameters(params_dict, template_models)
        
        # Setup supply and demand nodes with template-specific parameters
        graph = setup_supply_demand_parameters(graph, params_dict, template_models)
        
        # Setup edge mass flow (needed by all pipe templates)
        graph = setup_edge_mass_flow(graph, params_dict)
        
    except Exception as e:
        print(f"✗ Error in template parameter setup: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Step 6: Generate Modelica model
    print("\nStep 4: Modelica Model Generation")
    print("-" * 35)
    
    try:
        print("Creating Modelica model package...")
        sysmmodel = sysut.create_model(
            name="Seestadt_heating_network",
            save_at=dir_dest,
            graph=graph,
            stop_time=603900,        # Same duration as e11 examples (about 1 week)
            timestep=900,            # 15-minute time steps
            model_supply=template_models['supply'],
            model_demand=template_models['demand'], 
            model_pipe=template_models['pipe'],
            model_medium="AixLib.Media.Specialized.Water.ConstantProperties_pT",
            model_ground="t_ground_table", 
            T_nominal=273.15 + 80,   # Nominal temperature
            p_nominal=5e5,           # Nominal pressure (5 bar)
        )
        print("✓ Modelica model created successfully!")
        print(f"  Model name: Seestadt_heating_network")
        print(f"  Simulation time: {603900/3600:.1f} hours")
        print(f"  Time step: {900/60:.0f} minutes")
        print(f"  Model saved to: {dir_dest}")

        # Export system model graph for analysis
        json_path = os.path.join(dir_dest, "sysmmodel_graph.json")
        sysut.save_system_model_to_json(sysmmodel, json_path)
        print(f"  System model graph: {json_path}")
        
        return sysmmodel
        
    except Exception as e:
        print(f"✗ Error creating model: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return None


# Main function
if __name__ == "__main__":
    main()