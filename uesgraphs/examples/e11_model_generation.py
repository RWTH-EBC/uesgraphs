# -*- coding: utf-8 -*-
"""
This module demonstrates the generation of a Modelica models with uesmodels

!!! Run e10_networks before running this script !!!
"""

import datetime
import os
import uesgraphs.systemmodels.systemmodelheating as sysmh
import uesgraphs.systemmodels.utilities as sysut
from uesgraphs.uesgraph import UESGraph
import uesgraphs.utilities as ut


def main():
    start_time = datetime.datetime.now()

    # Make workspace
    workspace = ut.make_workspace("uesmodel_examples")
    dir_tests = os.path.join(workspace, "tests")
    dir_modelgen_base = os.path.abspath(os.path.join(dir_tests, "test_modelgen"))

    if not os.path.exists(workspace):
        os.mkdir(workspace)

    # Pinola Network
    network_pinola = "Pinola"

    print("Generating models for network {}".format(network_pinola))

    # Generate path to store created models
    dir_modelgen_pinola = os.path.join(dir_modelgen_base, network_pinola)
    workspace_pinola = os.path.join(workspace, network_pinola)

    # Creates `input`, `model`, `result` and `visualization` directories
    dir_input, dir_model, dir_result, dir_visualization = create_dirs(workspace_pinola)

    # Generate Modelica models of Pinola Network usig model_generation_pinola
    # function. There are two parameters needed. The source directory with
    # nodes.json 'dir_source' and the directory to store generated models
    # 'dir_dest'.
    model_generation_pinola(dir_modelgen_pinola, dir_model)

    # Ibpsa Network
    network_ibpsa = "Ibpsa"

    print("Generating models for network {}".format(network_ibpsa))

    # Generate path to store created models
    dir_modelgen_ibpsa = os.path.join(dir_modelgen_base, network_ibpsa)
    workspace_ibpsa = os.path.join(workspace, network_ibpsa)

    # Creates `input`, `model`, `result` and `visualization` directories
    dir_input, dir_model, dir_result, dir_visualization = create_dirs(workspace_ibpsa)

    # Generate Modelica models of Ibpsa Network usig model_generation_ibpsa
    # function. There are two parameters needed. The source directory with
    # nodes.json 'dir_source' and the directory to store generated models
    # 'dir_dest'.
    model_generation_ibpsa(dir_modelgen_ibpsa, dir_model)

    end_time = datetime.datetime.now()
    runtime = end_time - start_time
    print("runtime:", runtime)


def model_generation_pinola(dir_source, dir_dest):
    """Run example model generation for Pinola network

    Parameters
    ----------
    dir_source : str
        Source directory with nodes.json
    dir_dest : str
        Directory to store generated models
    """
    graph = UESGraph()

    # Import network from json input file using from_json function. Below the
    # network_type 'heating' is imported.
    graph.from_json(path=dir_source, network_type="heating")
    graph.graph["network_type"] = "heating"

    # To add data for model generation to the uesgraph the prepare_graph
    # funtion is used. There are thireen parameters available. Below the supply
    # temperature in K, supply pressure in Pa, return temperature in K,
    # return pressure in Pa, Design temperature difference over substation in K
    # and the nominal mass flow rate in kg/s are added to the graph.
    graph = sysut.prepare_graph(
        graph=graph,
        T_supply=[273.15 + 80],
        p_supply=6e5,
        T_return=273.15 + 50,
        p_return=2e5,
        dT_design=30,
        m_flow_nominal=1,
    )

    # To generate a generic Modelica model the create_model function is used.
    # There are 21 parameters available.
    sysut.create_model(
        name="Pinola_open_loop_dT_var",
        save_at=dir_dest,
        graph=graph,
        stop_time=603900,
        timestep=900,
        model_supply="AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        model_demand="AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
        model_pipe="AixLib.Fluid.FixedResistances.PlugFlowPipe",
        model_medium="AixLib.Media.Specialized.Water.ConstantProperties_pT",
        model_ground="t_ground_table",
        T_nominal=273.15 + 80,
        p_nominal=5e5,
    )
    # Switching to variable ground temperature with the Kusuda model. Below
    # the parameter model_ground is replaced by a kusuda model.
    sysut.create_model(
        name="Pinola_t_ground_var",
        save_at=dir_dest,
        graph=graph,
        stop_time=603900,
        timestep=900,
        model_supply="AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        model_demand="AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
        model_pipe="AixLib.Fluid.FixedResistances.PlugFlowPipe",
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
        name="Pinola_low_temp_network",
        save_at=dir_dest,
        graph=graph,
        stop_time=603900,
        timestep=900,
        model_supply="AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        model_demand="AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot",
        model_pipe="AixLib.Fluid.FixedResistances.PlugFlowPipe",
        model_medium="AixLib.Media.Specialized.Water.ConstantProperties_pT",
        model_ground="t_ground_kusuda",
        T_nominal=273.15 + 15,
        p_nominal=5e5,
    )


def model_generation_ibpsa(dir_source, dir_dest):
    """Run example model generation for Ibpsa network

    Parameters
    ----------
    dir_source : str
        Source directory with nodes.json
    dir_dest : str
        Directory to store generated models
    """
    graph = UESGraph()

    # Import network from json input file using from_json function. Below the
    # network_type 'heating' is imported.
    graph.from_json(path=dir_source, network_type="heating")
    graph.graph["network_type"] = "heating"

    # The uesgraph is prepared to generate a Modelica model by adding data
    # using the prepare_graph function.
    graph = sysut.prepare_graph(
        graph=graph,
        T_supply=[273.15 + 80],
        p_supply=6e5,
        T_return=273.15 + 50,
        p_return=2e5,
        dT_design=30,
        m_flow_nominal=1,
    )

    # A generic Modelica model is generated using the create_model function.
    sysut.create_model(
        name="Ibpsa_open_loop_dT_var",
        save_at=dir_dest,
        graph=graph,
        stop_time=603900,
        timestep=900,
        model_supply="AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        model_demand="AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
        model_pipe="AixLib.Fluid.FixedResistances.PlugFlowPipe",
        model_medium="AixLib.Media.Specialized.Water.ConstantProperties_pT",
        model_ground="t_ground_table",
        T_nominal=273.15 + 80,
        p_nominal=5e5,
    )
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
        model_pipe="AixLib.Fluid.FixedResistances.PlugFlowPipe",
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
        model_pipe="AixLib.Fluid.FixedResistances.PlugFlowPipe",
        model_medium="AixLib.Media.Specialized.Water.ConstantProperties_pT",
        model_ground="t_ground_kusuda",
        T_nominal=273.15 + 15,
        p_nominal=5e5,
    )


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
