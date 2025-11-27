# -*- coding: utf-8 -*-
"""
Comprehensive Mako Template Generation for UESGraphs Modelica Components
=====================================================================

This module demonstrates three different approaches to generating Mako templates 
for AixLib component types, providing a complete learning experience from manual 
step-by-step generation to automated production workflows.

Template Generation Methods:
---------------------------
1. **Manual Method**: Step-by-step individual template generation
   - Educational approach showing internal workings
   - Individual UESTemplates instantiation for each model
   - Custom save paths and immediate testing
   - Full visibility into the generation process

2. **Bulk Method**: Efficient batch generation
   - Single generate_bulk() call for multiple models
   - Organized error handling and reporting
   - Suitable for moderate-scale template generation

3. **Configuration-Driven Method**: Production-ready automation
   - Uses JSON configuration files
   - Environment variable integration
   - Rigorous mode for automated overwriting
   - Ideal for CI/CD and automated workflows

Component Types:
--------------
1. Demand Models:
   - Variable supply temperature models
   - Heat pump models with Carnot cycle
   - Closed-loop DHC substation models
   - Templates include parameters for temperature differences and nominal conditions

2. Pipe Models:
   - Static pipe model
   - Plug flow pipe models (standard and embedded)
   - Plug flow pipe with zeta value
   - DHC pipe models
   - Templates include thermal and geometric parameters

3. Supply Models:
   - Ideal source models for open-loop systems
   - DHC supply models with heater/cooler/storage
   - Templates include pressure and temperature parameters

Educational Progression:
----------------------
This example is designed for researchers and developers who want to understand:
- How template generation works internally (Manual Method)
- How to efficiently generate multiple templates (Bulk Method) 
- How to set up automated template generation workflows (Config Method)

Requirements:
-----------
- AixLib v2.1.0+ library installation
- UESGraphs package with systemmodels module
- Shapely for geometric operations
- Optional: AIXLIB_LIBRARY_PATH environment variable for automated workflows

Usage:
-----
Run the script and select from four demonstration modes:
1. Manual demonstration - See step-by-step template creation
2. Bulk demonstration - See efficient batch processing  
3. Config demonstration - See automated configuration-driven generation
4. All methods - Experience the complete progression
"""

from uesgraphs.systemmodels.templates import UESTemplates
import shapely.geometry as sg
import os
import tkinter as tk
import tkinter.filedialog as filedialog

from uesgraphs.examples import e1_readme_example as e1


def get_test_data(model_type: str, model_name: str):
    """Get sample test data for different model types"""
    base_data = {
        "position": sg.Point(64.76, 217.14),
        "comp_model": model_name,
    }
    
    if model_type == "Demand":
        return {
            **base_data,
            "name": "B1",
            "node_type": "building",
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
            "m_flo_bypass": 0.5,
            "Q_flow_nominal": 22719.1187448,
            "TReturn": 323.15,
            "_dp_start": 20,
        }
    elif model_type == "Pipe":
        return {
            **base_data,
            "name": "P1",
            "node_type": "pipe",
            "m_flow_nominal": 10,
            "length": 666,
            "dIns": 0.05,
            "kIns": 0.0032,
            "nPorts": 2,
        }
    elif model_type == "Supply":
        return {
            **base_data,
            "name": "S1",
            "node_type": "building",
            "is_supply_heating": True,
            "is_supply_cooling": False,
            "is_supply_electricity": False,
            "is_supply_gas": False,
            "is_supply_other": False,
            "has_table": False,
            "pReturn": 20000,
            "TReturn": 293.15,
        }
    
    return None


def demonstrate_manual_generation(path_aixlib: str, workspace: str):
    """
    Method 1: Manual step-by-step template generation

    This approach shows exactly how template generation works internally.
    Each template is created individually with full control over the process.
    This is the best method for learning and debugging.

    Returns:
        int: Number of successfully generated templates
    """
    print("\n" + "="*70)
    print("METHOD 1: MANUAL TEMPLATE GENERATION")
    print("="*70)
    print("This method demonstrates step-by-step individual template creation.")
    print("You'll see exactly how each template is generated and tested.")

    # Define models for manual generation (smaller set for clarity)
    manual_models = {
        "Demand": ["AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp"],
        "Pipe": ["AixLib.Fluid.DistrictHeatingCooling.Pipes.StaticPipe"],
        "Supply": ["AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal"]
    }

    total_models = sum(len(models) for models in manual_models.values())
    successful = 0

    print(f"\nGenerating {total_models} templates manually...")

    # Process each model type individually
    for model_type, model_names in manual_models.items():
        print(f"\n--- Processing {model_type} Models ---")

        for model_name in model_names:
            print(f"\nStep 1: Creating UESTemplates instance for {model_name}")
            template_gen = UESTemplates(model_name=model_name, model_type=model_type)

            # Custom save path (demonstrates flexibility of manual approach)
            custom_path = os.path.join(workspace, "manual_" + model_name.replace(".", "_") + ".mako")
            template_gen.save_path = custom_path
            print(f"Step 2: Setting custom save path to {custom_path}")

            print(f"Step 3: Generating new template from AixLib library...")
            try:
                template_gen.generate_new_template(path_library=path_aixlib)
                print(f"SUCCESS: Template generated successfully")
                successful += 1

                # Immediate testing (advantage of manual approach)
                print(f"Step 4: Testing template with sample data...")
                test_data = get_test_data(model_type, model_name)

                if test_data:
                    # Create fresh instance for rendering
                    render_gen = UESTemplates(model_name=model_name, model_type=model_type)
                    mo = render_gen.render(node_data=test_data, i=1, number_of_instances=1)

                    # Show full generated code (educational value)
                    print(f"SUCCESS: Template test successful!")
                    print(f"Generated Modelica code ({len(mo)} characters):")
                    print("-" * 50)
                    print(mo[:300] + "..." if len(mo) > 300 else mo)
                    print("-" * 50)
                else:
                    print(f"WARNING: No test data available for {model_type}")

            except Exception as e:
                print(f"FAILED: Error generating template: {e}")

    print(f"\n--- Manual Generation Summary ---")
    if successful > 0:
        print(f"SUCCESS: {successful}/{total_models} templates generated successfully")
        print(f"Templates saved in: {workspace}")
    else:
        print(f"FAILED: No templates were generated successfully ({successful}/{total_models})")

    return successful


def demonstrate_bulk_generation(path_aixlib: str, workspace: str):
    """
    Method 2: Bulk template generation

    This approach uses the generate_bulk() method to efficiently create
    multiple templates with organized error handling. Good for moderate
    scale template generation.

    Returns:
        int: Number of successfully generated templates
    """
    print("\n" + "="*70)
    print("METHOD 2: BULK TEMPLATE GENERATION")
    print("="*70)
    print("This method demonstrates efficient batch processing of multiple templates.")
    print("Better error handling and reporting compared to manual approach.")

    # Extended model set for bulk generation
    bulk_models = {
        "Demand": [
            "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
            "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot",
        ],
        "Pipe": [
            "AixLib.Fluid.DistrictHeatingCooling.Pipes.StaticPipe",
            "AixLib.Fluid.FixedResistances.PlugFlowPipe",
            "AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeZeta",
        ],
        "Supply": [
            "AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        ]
    }

    total_models = sum(len(models) for models in bulk_models.values())
    print(f"\nGenerating {total_models} templates using bulk method...")

    # Single call to generate all templates
    print("Calling UESTemplates.generate_bulk()...")
    results = UESTemplates.generate_bulk(
        bulk_models,
        path_aixlib,
        workspace=workspace
    )

    # Organized result reporting
    print(f"\n--- Bulk Generation Results ---")
    successful = sum(1 for result in results.values() if not result.startswith("ERROR"))
    print(f"Successfully generated: {successful}/{total_models} templates")

    if successful > 0:
        print("\nSUCCESS: Successful templates:")
        for model_name, result in results.items():
            if not result.startswith("ERROR"):
                print(f"  • {model_name}")

    if successful < total_models:
        print("\nFAILED: Failed templates:")
        for model_name, result in results.items():
            if result.startswith("ERROR"):
                print(f"  • {model_name}: {result}")

    # Test rendering for successful templates
    if successful > 0:
        print(f"\n--- Testing Template Rendering ---")
        tested = 0
        for model_type, model_names in bulk_models.items():
            for model_name in model_names:
                if model_name in results and not results[model_name].startswith("ERROR"):
                    test_data = get_test_data(model_type, model_name)
                    if test_data:
                        try:
                            template_gen = UESTemplates(model_name=model_name, model_type=model_type)
                            mo = template_gen.render(node_data=test_data, i=1, number_of_instances=1)
                            tested += 1
                            print(f"SUCCESS: {model_name} - Rendered {len(mo)} characters")
                        except Exception as e:
                            print(f"FAILED: {model_name} - Render error: {e}")

        print(f"\n--- Bulk Generation Summary ---")
        print(f"SUCCESS: {tested} templates tested successfully")
        print(f"Templates saved in: {workspace}")
    else:
        print(f"\n--- Bulk Generation Summary ---")
        print(f"FAILED: No templates were generated successfully")

    return successful


def demonstrate_config_generation(workspace: str):
    """
    Method 3: Configuration-driven template generation

    This approach uses JSON configuration files and environment variables
    for fully automated template generation. Ideal for production workflows
    and CI/CD integration.

    Returns:
        int: Number of successfully generated templates
    """
    print("\n" + "="*70)
    print("METHOD 3: CONFIGURATION-DRIVEN GENERATION")
    print("="*70)
    print("This method demonstrates automated template generation from configuration.")
    print("Uses JSON files and environment variables - ideal for production use.")

    # Check for environment variable (production approach)
    aixlib_env = os.environ.get('AIXLIB_LIBRARY_PATH')
    if aixlib_env:
        print(f"SUCCESS: Found AIXLIB_LIBRARY_PATH environment variable: {aixlib_env}")
        path_info = "environment variable"
    else:
        print("WARNING: AIXLIB_LIBRARY_PATH not set - will use interactive file selection")
        path_info = "interactive selection"

    config_file = "data/templates/template_aixlib_components.json"
    print(f"Using configuration file: {config_file}")

    try:

        # Rigorous mode (automated overwriting)
        print(f"\n--- Rigorous Mode ---")
        print("Regenerating with rigorous mode (auto-overwrite for automation)...")
        results_rigorous = UESTemplates.generate_from_config(
            config_file,
            workspace=workspace,
            rigorous=True  # Flag that enforces overwriting
        )

        # Report final results
        successful = sum(1 for result in results_rigorous.values() if not result.startswith("ERROR"))
        total = len(results_rigorous)

        print(f"\n--- Configuration Generation Results ---")
        print(f"Successfully generated: {successful}/{total} templates")
        print(f"AixLib path source: {path_info}")

        if successful > 0:
            print(f"\nSUCCESS: Successfully generated templates:")
            for model_name, template_path in results_rigorous.items():
                if not template_path.startswith("ERROR"):
                    print(f"  • {model_name}")
            print(f"\nTemplates saved in: {workspace}")

        if successful < total:
            print(f"\nFAILED: Failed templates:")
            for model_name, result in results_rigorous.items():
                if result.startswith("ERROR"):
                    print(f"  • {model_name}: {result}")

        if successful == 0:
            print(f"\nFAILED: No templates were generated successfully")

        return successful

    except Exception as e:
        print(f"FAILED: Configuration generation failed: {e}")
        print("This might happen if the JSON config file is not found or AixLib path is invalid.")
        return 0


def get_user_choice():
    """Get user's choice for demonstration method"""
    print("\n" + "="*70)
    print("UESGRAPHS TEMPLATE GENERATION DEMONSTRATION")
    print("="*70)
    print("Choose a demonstration method:")
    print("1. Manual Method - Step-by-step individual template generation (Educational)")
    print("2. Bulk Method - Efficient batch processing (Practical)")
    print("3. Config Method - Automated configuration-driven generation (Production)")
    print("4. All Methods - Complete demonstration of all approaches")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice in ['1', '2', '3', '4', '5']:
                return int(choice)
            else:
                print("Please enter a number between 1 and 5.")
        except KeyboardInterrupt:
            print("\nExiting...")
            return 5


def get_aixlib_path():
    """Get AixLib library path via file dialog"""
    print("\n--- AixLib Library Path Selection ---")
    
    print(" A file dialog will open to select the AixLib 'package.mo' file. If you cant see it, check all open windows.")
    # Hide the root Tkinter window
    root = tk.Tk()
    root.withdraw()
    
    # Open file dialog
    path_aixlib = filedialog.askopenfilename(
        title="Select AixLib package.mo file",
        filetypes=[("Modelica package file", "package.mo")]
    )
    
    if path_aixlib:
        print(f"SUCCESS: Selected AixLib path: {path_aixlib}")
        return path_aixlib
    else:
        print("FAILED: No file selected.")
        return None


def main():
    """Main function with method selection"""
    choice = get_user_choice()

    if choice == 5:
        print("Goodbye!")
        return

    # Create workspace
    workspace = e1.workspace_example("e12")
    print(f"SUCCESS: Created workspace: {workspace}")

    # Get AixLib path for methods that need it
    path_aixlib = None
    if choice in [1, 2, 4]:
        path_aixlib = get_aixlib_path()
        if not path_aixlib:
            print("AixLib path is required for the selected method(s). Exiting.")
            return

    # Execute selected demonstration(s) and track success
    total_successful = 0

    if choice == 1:
        total_successful = demonstrate_manual_generation(path_aixlib, workspace)
    elif choice == 2:
        total_successful = demonstrate_bulk_generation(path_aixlib, workspace)
    elif choice == 3:
        total_successful = demonstrate_config_generation(workspace)
    elif choice == 4:
        # All methods demonstration
        print("\n🚀 Running complete demonstration of all template generation methods...")
        manual_success = demonstrate_manual_generation(path_aixlib, workspace)
        bulk_success = demonstrate_bulk_generation(path_aixlib, workspace)
        config_success = demonstrate_config_generation(workspace)
        total_successful = manual_success + bulk_success + config_success

        print("\n" + "="*70)
        print("COMPLETE DEMONSTRATION FINISHED")
        print("="*70)
        print("You have now seen all three approaches to template generation:")
        print("• Manual: Best for learning and debugging")
        print("• Bulk: Best for moderate-scale generation")
        print("• Config: Best for production and automation")
        print(f"\nTotal templates generated across all methods: {total_successful}")

    # Final summary
    print("\n" + "="*70)
    if total_successful > 0:
        print(f"SUCCESS: {total_successful} template(s) generated successfully")
        print(f"Templates saved to: {workspace}")
    else:
        print("FAILED: No templates were generated successfully")
        print("Please check the error messages above for details")
    print("="*70)


if __name__ == "__main__":
    main()