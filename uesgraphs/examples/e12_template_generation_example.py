# -*- coding: utf-8 -*-
"""
Mako Template Generation for UESGraphs Modelica Components
====================================================

This module demonstrates the generation of Mako templates for different AixLib 
component types, which are required for automated Modelica code generation using 
UESGraphs. Templates are generated for demands, pipes, and supplies based on 
AixLib v2.1.0 components.

Component Types:
-------------
1. Demand Models:
   - Variable supply temperature model
   - Heat pump model with Carnot cycle
   - Templates include parameters for temperature differences and nominal conditions

2. Pipe Models:
   - Static pipe model
   - Plug flow pipe model
   - Plug flow pipe with zeta value
   - Templates include thermal and geometric parameters

3. Supply Models:
   - Ideal source model for open-loop systems
   - Templates include pressure and temperature parameters

Template Generation Process:
-------------------------
For each component type (demand, pipe, supply):
1. Creates a UESTemplates instance for the specific model
2. Generates a new template from AixLib library
3. Tests the template with sample data
4. Generates corresponding Modelica code

Generated templates follow the Mako syntax and include:
- Component-specific parameters
- Geometric information
- Operating conditions
- Connection specifications

Test Cases:
---------
- Demand: Building with defined heat demand and temperature levels
- Pipe: Standard pipe with insulation parameters
- Supply: Ideal source with return conditions

Requirements:
-----------
- AixLib v2.1.0 library must be installed and path must be provided
- UESGraphs package with systemmodels module
- Shapely for geometric operations

Notes:
-----
- Templates are saved with .mako extension
- Generated Modelica code is printed to console for verification
- Template paths are customizable for demonstration purposes
- Default template storage is in uesgraphs/data/templates
"""

from uesgraphs.systemmodels.templates import UESTemplates
import shapely.geometry as sg
import os
import tkinter as tk
import tkinter.filedialog as filedialog

from uesgraphs.examples import e1_readme_example as e1

def main():

    # Hide the root Tkinter window
    root = tk.Tk()
    root.withdraw()
    
    # Open a file dialog to select the package.mo file
    path_aixlib = filedialog.askopenfilename(
        title="Select AixLib package.mo file",
        filetypes=[("Modelica package file", "package.mo")]
    )
    
    if path_aixlib:
        print(f"You have selected: {path_aixlib}")
        # Now you can use path_aixlib in your code
    else:
        print("No file selected.")

    # Create e12 directory in the workspace
    workspace = e1.workspace_example("e12")

    demand_models = [
        "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
        "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot",
    ]

    # create and test demand models
    for model_name in demand_models:
        template_gen = UESTemplates(model_name=model_name, model_type="Demand")
        
        #Path usually set to uesgraphs/data/templates, will be overwritten for demonstration
        template_gen.save_path = os.path.join(workspace, model_name.replace(".", "_") + ".mako")
        
        template_gen.generate_new_template(path_library=path_aixlib)

        test_demand = {
            "name": "B1",
            "node_type": "building",
            "position": sg.Point(64.76, 217.14),
            "is_supply_heating": False,
            "is_supply_cooling": False,
            "is_supply_electricity": False,
            "is_supply_gas": False,
            "is_supply_other": False,
            "has_table": False,
            "dTDesign": 30,
            "dTBuilding": 10,
            "TSupplyBuilding": 70,
            "m_flow_nominal": 10,
            "m_flo_bypass": 0.5,    # for Bypass Template
            "Q_flow_nominal": 22719.1187448,
            "TReturn": 323.15,
            "_dp_start": 20,
            "comp_model": model_name,
        }

        template_gen = UESTemplates(model_name=test_demand["comp_model"], model_type="Demand")
        mo = template_gen.render(node_data=test_demand, i=1, number_of_instances=1)
        print(mo)

    # Names of Pipe models
    pipe_models = [
        "AixLib.Fluid.DistrictHeatingCooling.Pipes.StaticPipe",
        "AixLib.Fluid.FixedResistances.PlugFlowPipe",
        "AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeZeta",
    ]
    # create and test pipe models
    for model_name in pipe_models:
        template_gen = UESTemplates(model_name=model_name, model_type="Pipe")

        #Path usually set to uesgraphs/data/templates, will be overwritten for demonstration
        template_gen.save_path = os.path.join(workspace, model_name.replace(".", "_") + ".mako")

        template_gen.generate_new_template(path_library=path_aixlib)

        test_pipe = {
            "name": "P1",
            "node_type": "pipe",
            "position": sg.Point(64.76, 217.14),
            "m_flow_nominal": 10,
            "length": 666,
            "dIns": 0.05,
            "kIns": 0.0032,
            "nPorts": 2,
            "comp_model": model_name,
        }
        template_gen = UESTemplates(model_name=test_pipe["comp_model"], model_type="Pipe")
        mo = template_gen.render(node_data=test_pipe, i=1, number_of_instances=1)
        print(mo)

    # Names of Supply models
    supply_models = [
        "AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
    ]
    # create and test supply models
    for model_name in supply_models:
        template_gen = UESTemplates(model_name=model_name, model_type="Supply")

        #Path usually set to uesgraphs/data/templates, will be overwritten for demonstration
        template_gen.save_path = os.path.join(workspace, model_name.replace(".", "_") + ".mako")
        
        template_gen.generate_new_template(path_library=path_aixlib)

        test_supply = {
            "name": "S1",
            "node_type": "building",
            "position": sg.Point(64.76, 217.14),
            "is_supply_heating": True,
            "is_supply_cooling": False,
            "is_supply_electricity": False,
            "is_supply_gas": False,
            "is_supply_other": False,
            "has_table": False,
            "pReturn": 20000,
            "TReturn": 293.15,
            "comp_model": model_name,
        }
        template_gen = UESTemplates(model_name=test_supply["comp_model"], model_type="Supply")
        mo = template_gen.render(node_data=test_supply, i=1, number_of_instances=1)
        print(mo)


if __name__ == "__main__":
    main()
