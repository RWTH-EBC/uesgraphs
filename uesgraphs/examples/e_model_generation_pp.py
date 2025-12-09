# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
"""
Modelica Model Generation using UESGraphs
=======================================

This module demonstrates the automated generation of Modelica models for district heating 
networks. The generated models can be directly simulated in Dymola, but require exactly 
AixLib version 2.1.0. Other versions are not compatible and will cause simulation errors.

Model Variants:
-------------
For each network (Pinola and IBPSA), three model variants are generated:

1. Open Loop with Variable Supply Temperature (suffix: _open_loop_dT_var)
   - High temperature network (80°C supply / 50°C return)
   - Table-based ground temperature
   - Direct heating substations

2. Variable Ground Temperature Model (suffix: _t_ground_var)
   - Same as variant 1 but uses Kusuda ground temperature model
   - More detailed soil temperature calculation

3. Low Temperature Network (suffix: _low_temp_network)
   - Low temperature regime (20°C supply / 10°C return)
   - Heat pump substations (Carnot-based)
   - Includes substation parameters (COP, nominal temperatures)

Functions:
---------
model_generation_pinola(dir_source, dir_dest):
    Generates three variants of Modelica models for the Pinola network

model_generation_ibpsa(dir_source, dir_dest):
    Generates three variants of Modelica models for the IBPSA network

create_dirs(dir_project):
    Creates standardized directory structure for model files and results

Model Parameters:
---------------
- Simulation time: 603900 seconds
- Time step: 900 seconds
- Nominal pressure: 5e5 Pa
- Heat pump COP (nominal): 4.5
- Network pressure difference: 4e5 Pa (supply-return)

Components Used:
-------------
- Supply: AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal
- Demand: AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp
         AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot
- Pipes: AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded
- Medium: AixLib.Media.Specialized.Water.ConstantProperties_pT

Notes:
-----
- All models use plug flow pipe models with embedded heat losses
- Ground coupling can be either table-based or using the Kusuda model
- Directory structure is automatically created for inputs, models, and results
- Models are exported in Modelica format (.mo files)
- Direct simulation in Dymola is possible, but strictly requires AixLib v2.1.0
"""

import datetime
import os
import uesgraphs.systemmodels_pp.utilities as sysut
import uesgraphs as ug
from uesgraphs.uesgraph import UESGraph
import uesgraphs.utilities as ut


from uesgraphs.examples import e1_readme_example as e1
from uesgraphs.examples import e10_networks_example as e10
def main():
    start_time = datetime.datetime.now()

    # Make workspace
    workspace = ut.make_workspace("uesmodel_examples")
    workspace = e1.workspace_example("e17")
    dir_tests = os.path.join(workspace, "inputs")
    dir_modelgen_base = os.path.abspath(os.path.join(dir_tests, "test_modelgen"))
    os.makedirs(dir_modelgen_base, exist_ok=True)

    # Ibpsa Network
    network_ibpsa = "Ibpsa"

    print("Generating models for network {}".format(network_ibpsa))

    e10.make_network_ibpsa(os.path.join(dir_modelgen_base, network_ibpsa))

    # Generate path to store created models
    dir_modelgen_ibpsa = os.path.join(dir_modelgen_base, network_ibpsa)
    workspace_ibpsa = os.path.join(workspace, network_ibpsa)

    # Creates `input`, `model`, `result` and `visualization` directories
    dir_input, dir_model, dir_result, dir_visualization = create_dirs(workspace_ibpsa)

    # Generate Modelica models of Ibpsa Network usig model_generation_ibpsa
    # function. There are two parameters needed. The source directory with
    # nodes.json 'dir_source' and the directory to store generated models
    # 'dir_dest'.
    model_generation_ibpsa(dir_modelgen_ibpsa, dir_model, workspace)



    end_time = datetime.datetime.now()
    runtime = end_time - start_time
    print("runtime:", runtime)


def model_generation_ibpsa(dir_source, dir_dest, workspace):
    '''Run example model generation for Ibpsa network

    Parameters
    ----------
    dir_source : str
        Source directory with nodes.json
    dir_dest : str
        Directory to store generated models
    '''
    graph = UESGraph()

    # Import network from json input file using from_json function. Below the
    # network_type 'heating' is imported.
    graph.from_json(path=dir_source, network_type="heating")
    graph.graph["name"] = "IBPSA"
    graph.graph["network_type"] = "heating"
    graph.graph["supply_type"] = "supply"

    # The uesgraph is prepared to generate a Modelica model by adding data
    # using the prepare_graph function.
    graph = sysut.prepare_graph(
        graph=graph,
        T_supply=[273.15 + 80],
        p_supply=6e5/100000,
        T_return=273.15 + 50,
        p_return=2e5/100000,
        dT_design=30,
    )

    # A generic Modelica model is generated using the create_model function.
    model, graph = sysut.create_model(
        name="Ibpsa_open_loop_dT_var",
        save_at=dir_dest,
        graph=graph,
        stop_time=603900,
        timestep=900,
    )

    vis = ug.Visuals(graph)
    for edge in graph.edges:
        graph.edges[edge]["m_flow_mean"] = graph.edges[edge]["m_flow"].mean()
    vis.show_network(show_plot=False,
                           scaling_factor=1,
                           scaling_factor_diameter=50,
                           label_size=15,
                           ylabel="Mean mass flow [kg/s]",
                           generic_extensive_size="m_flow_mean",
                           save_as=os.path.join(workspace, "m_flow.png"),
                           timestamp=f"{graph.graph["name"]}: Mean mass flow"
                           )
    
    for node in graph.nodes:
        graph.nodes[node]["press_mean"] = graph.nodes[node]["pressure"].mean()
    vis.show_network(show_plot=False,
                           scaling_factor=1,
                           scaling_factor_diameter=50,
                           ylabel="Mean pressure [Pa]",
                           label_size=15,
                           generic_intensive_size="press_mean",
                           save_as=os.path.join(workspace, "pressure.png"),
                           timestamp=f"{graph.graph["name"]}: Mean pressure"
                           )

"""
    # Switching to variable ground temperature with the Kusuda model. Below
    # the parameter model_ground is replaced by a kusuda model.
    sysut.create_model(
        name="Ibpsa_t_ground_var",
        save_at=dir_dest,
        graph=graph,
        stop_time=603900,
        timestep=900,
        model_supply="AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        model_demand="AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
        model_pipe="AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded",
        model_medium="AixLib.Media.Specialized.Water.ConstantProperties_pT",
        model_ground="t_ground_kusuda",
        T_nominal=273.15 + 80,
        p_nominal=5e5,
    )
    # Prepare and create a model for a low temperature heating network using
    # heat pump substations
    graph = sysut.prepare_graph(
        graph=graph,
        T_supply=[273.15 + 20],
        p_supply=6e5,
        T_return=273.15 + 10,
        p_return=2e5,
        dT_design=10,
        m_flow_nominal=1,
        dp_nominal=50000,
        dT_building=10,
        T_supply_building=273.15 + 40,
        cop_nominal=4.5,
        T_con_nominal=273.15 + 35,
        T_eva_nominal=273.15 + 10,
    )

    sysut.create_model(
        name="Ibpsa_low_temp_network",
        save_at=dir_dest,
        graph=graph,
        stop_time=603900,
        timestep=900,
        model_supply="AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        model_demand="AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot",
        model_pipe="AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded",
        model_medium="AixLib.Media.Specialized.Water.ConstantProperties_pT",
        model_ground="t_ground_kusuda",
        T_nominal=273.15 + 15,
        p_nominal=5e5,
    )
"""
def create_dirs(dir_project):
    """Creates `input`, `model`, `result` and `visualization` directories

    Parameters
    ----------
    dir_project : str
        Base directory of the example where the directories will be created

    Returns
    -------
    dir_input : str
        Directory for input files
    dir_model : str
        Directory for model files
    dir_result : str
        Directory for result files
    dir_visualization : str
        Directory for plots
    """
    if not os.path.exists(dir_project):
        os.mkdir(dir_project)

    dir_input = os.path.join(dir_project, "input")
    if not os.path.exists(dir_input):
        os.mkdir(dir_input)
    dir_result = os.path.join(dir_project, "result")
    if not os.path.exists(dir_result):
        os.mkdir(dir_result)
    dir_model = os.path.join(dir_project, "model")
    if not os.path.exists(dir_model):
        os.mkdir(dir_model)
    dir_visualization = os.path.join(dir_project, "visualization")
    if not os.path.exists(dir_visualization):
        os.mkdir(dir_visualization)
    dir_design = os.path.join(dir_input, "design")
    if not os.path.exists(dir_design):
        os.mkdir(dir_design)

    return dir_input, dir_model, dir_result, dir_visualization


# Main function
if __name__ == "__main__":
    main()
