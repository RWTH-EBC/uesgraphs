import json
from typing import Dict, List, Tuple
import os

from uesgraphs.systemmodels.templates import UESTemplates
from uesgraphs.systemmodels.templates import ModelInfoExtractor

## How to generate templates for different libraries
"""
This script needs the path to a local modelica library and a json file where the components are defined. If custom_library is not used, the script will try to use AixLib.
The script will generate templates for all components defined in the json file. The json file should have the following structure:
    1. A "base_paths" object containing the root-paths to different component categories as Key-Value pairs:

    Keys are component categories (like "Demand", "Supply", "Pipe")
    Values are strings representing the base Modelica package paths (e.g., "AixLib.Fluid.DistrictHeatingCooling.Demands.")

    2. A "models" object containing the relative path from the root path to a certain component as key-value pairs where:

    Keys match the same component categories as in "base_paths" (e.g., "Demand", "Supply", "Pipe")
    Values are arrays of strings, each representing a specific model path relative to its base path (e.g., "ClosedLoop.DHCSubstationHeatPumpChiller")

    Look at /data/template_aixlib_components.json for an example.
"""

path_aixlib = ""
custom_library = None # Set to None if AixLib should be used. Set to the path of the custom library if a custom library should be used.
custom_models = None # Set to "data/template_custom_components.json" or other path where the custom models are defined.
### Note
"""
AixLib should be a system environment variable. If it is not, the path to the AixLib library should be set manually.
For other libraries, the path should be set manually and the components should be defined in a JSON file.
"""


def set_aixlib_path(path=None):
    global path_aixlib
    if path is None:
        try:
            path = os.environ['AIXLIB_LIBRARY_PATH']
        except KeyError:
            raise KeyError("Error: The environment variable AIXLIB_LIBRARY_PATH is not set.\n"
                           "Please set the path to the AixLib library in the environment variables.")
    path = path.replace("\\", "/")
    path = path + "/package.mo"
    path_aixlib = path

def load_models(config_file: str = 'data/template_components.json') -> Dict[str, Tuple[List[str], List[str]]]:
    """
    Loads model configurations from a JSON file and creates path references for different model types.

    The function expects a JSON file with the following structure:
    {
        "base_paths": {
            "model_type1": "path/to/base1/",
            "model_type2": "path/to/base2/"
        },
        "models": {
            "model_type1": ["model1", "model2"],
            "model_type2": ["model3", "model4"]
        }
    }

    Args:
        config_file (str): Relative path to the JSON configuration file.
                          Defaults to 'data/template_components.json'.

    Returns:
        Dict[str, Tuple[List[str], List[str]]]: A dictionary with model types as keys.
            Each value is a tuple containing:
            - List of complete model paths (base_path + model)
            - List of original model names

    Raises:
        FileNotFoundError: If the specified configuration file is not found.
        JSONDecodeError: If the file is not in valid JSON format.
        KeyError: If required keys are missing in the configuration.

    Example:
        >>> result = load_models()
        >>> # Example output:
        >>> # {
        >>> #     "model_type1": (
        >>> #         ["path/to/base1/model1", "path/to/base1/model2"],
        >>> #         ["model1", "model2"]
        >>> #     )
        >>> # }
    """

    dir_here = os.path.dirname(os.path.abspath(__file__))
    try:
        with open(os.path.join(dir_here, config_file), 'r') as file:
            config = json.load(file)
        
        base_paths = config['base_paths']
        models = config['models']
        
        result = {}
        for model_type in models:
            full_paths = [base_paths[model_type] + model for model in models[model_type]]
            result[model_type] = (full_paths, models[model_type])
        
        return result
    except FileNotFoundError:
        print(f"Error: The file {config_file} was not found.")
    except json.JSONDecodeError:
        print(f"Error: The file {config_file} is not valid JSON.")
    except KeyError as e:
        print(f"Error: The key {e} is missing in the configuration file.")
    
    return {}

def main(custom_library: str = None, custom_models: str = None, rigorous: bool = False, workspace: str = None):    
    if custom_library:
        libs_to_load = [custom_library]
        models = custom_models
    else:
        set_aixlib_path()
        libs_to_load = [path_aixlib]
        models = "data/template_aixlib_components.json"
    
    
    #1. Load path to models
    all_models = load_models(models)
    for model_type, (full_paths, model_names) in all_models.items():
        for full_path in full_paths:
            print(f"Generating template for {model_names}")
            template = UESTemplates(model_name=full_path, model_type=model_type) 
            template.rigorous = rigorous #Use true to natively overwrite existing templates
            if workspace is not None:
                template.save_path = os.path.join(workspace, full_path.replace(".", "_") + ".mako")
            
            template.generate_new_template(path_library=libs_to_load)
    
if __name__ == '__main__':
    main()