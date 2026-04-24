"""
Example for analyzing pandapipes simulation results using the analysis_pp class.
==============================================================

This example demonstrates the workflow if for analyzing pandapipes simulation results using the analysis_pp class.
Ensure that this example is run after completing E17, which generates the necessary simulation results and UESGraph JSON files for analysis.

Here are the steps covered in this example:
1. **Setup Workspace and Paths**: 
    Create a local workspace for this example and define paths to the simulation results generated in E17.
2. **Generate analysis class and run analysis**: 
    Create an instance of the analysis_pp class with the path to the simulation results and optionally set the timestep. 
    Then, call the thermal_loss_analysis and pump_power_analysis methods to perform the analyses.
    Also pipe_plots allows a deeper analysis of the pipe results, so you get plots of all avaible simulation variables for the whole timeseries. 
    You can use retransform_pipe_geojson_data to retransform the data to the geojson that is used.
    Also visualize_network allows you to visualize pressures, temperatures and mass flows of the whole district for a specific timestep,
    which is the index of the saved timeseries data.
    For the pump power analysis a parameter eta_total is set to 0.65, 
    adjust this value as needed for your specific system by setting it in the method call.
3. **Summary and Next Steps**:
    Summarize the results printed in the terminal and suggest next steps for further analysis or visualization.

"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to ensure imports work from local development
script_dir = os.path.dirname(os.path.abspath(__file__))
uesgraphs_root = os.path.dirname(os.path.dirname(script_dir))
if uesgraphs_root not in sys.path:
    sys.path.insert(0, uesgraphs_root)

from uesgraphs.analyze.analysis_pp import analysis_pp


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
    print("E18: Pandapipes simulation to analyze results")
    print("="*80)

    # =========================================================================
    # STEP 1: Setup Workspace and Paths
    # =========================================================================
    print("\n STEP 1: Setting up workspace and paths...")

    # Create workspace directory for this example
    workspace = workspace_example("e17")
    print(f"   Workspace: {workspace}")

    # Define paths to input files (these should have been generated in E17)
    sim_path = os.path.join(workspace, "models", "Sim20260424_111501") # Example path - adjust if your simulation results are in a different location

    print("   ✓ All paths configured")

    # =========================================================================
    # STEP 2: Generate analysis class and run analysis
    # =========================================================================
    print(f"\n   Simulation results path: {sim_path}")

    print("\n   Start analysis by creating an analysis class.\n")
    analysis = analysis_pp(root_path=Path(sim_path))

    try:
        print("\n   Running thermal loss analysis...")
        analysis.thermal_loss_analysis() 

        print("\n   Running pump power analysis...")
        analysis.pump_power_analysis()

        #print("\n   Running analysis plots for pipes...")
        #analysis.pipe_plots()
        # Adjust uesgraphs/analyze/analysis_pp.py if not all plots are needed or if you want to customize the plots
        # Is commented out by default because it generates a lot of plots

        print("\n   Running retransformation of data...")
        
        base_path = Path(__file__).resolve().parent
        file_path = base_path / ".." / "data" / "examples" / "e15_geojson" / "network.geojson"
        analysis.retransform_pipe_geojson_data(geojson_path=file_path)

        print("\n   Running visualize network...")
        analysis.visualize_network(time_index=487)

    except Exception as e:
        print(f"\n    ERROR: Analysis failed with: {e}")
        print("    Check the log file for detailed error information")
        raise

    # =========================================================================
    # STEP 3: Summary and Next Steps
    # =========================================================================
    print("\n" + "="*80)
    print(" E18 Example Completed Successfully!")
    print("="*80)

    print(f"\n What was printed:")
    print(f"   - Values for the system peak loss and annual loss in the thermal loss analysis")
    print(f"   - Values for the node temperature differences in the node temperature analysis")

    print("\n" + "="*80)



if __name__ == "__main__":
    print("\n" + "="*80)
    print("UESGraphs Example 18: Analyzing pandapipes simulation results using analysis_pp class")
    print("="*80)

    main()

    print("\n" + "="*80)
    print("Example script completed. Check your Terminal for printed results!")
    print("="*80 + "\n")
