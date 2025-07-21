# -*- coding: utf-8 -*-
"""
This module includes the UESModel graph to write Modelica code from uesgraphs
"""

import os
import sys
from mako.template import Template

#For logging
import logging
import tempfile
from datetime import datetime


import keyword
import re

# For type declaration in methods
from typing import List, Tuple, Any

from uesgraphs import get_versioning_info


def check_variable_name(name, max_attempts = 5):
    attempts = 0
    while attempts < max_attempts:
        if keyword.iskeyword(name) or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            if keyword.iskeyword(name):
                print(f"\n **** Error {name} is a reserved keyword in Python. ****\n")
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
                print(f"\n**** Error {name} is not a valid variable name. ****\n")
            print("Please enter a new variable name:\n"
                         "Regard that this name is only used by python and not in the modelica model.")
            name = input("Enter new variable name: ")
            attempts += 1
        else:
            return name

def set_up_logger(name,log_dir = None,level=int(logging.ERROR)):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if log_dir == None:
            log_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
        print(f"Logfile findable here: {log_file}")
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger   


class UESTemplates:
    """A class to handle templates for model generation with uesgraphs.

        Attributes
        ----------
        model_name : str
            Name of the modelica model.
            (e.g. AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal)
        model_type : str
            Choose from [Supply, Demand, Pipe]
        template_path : str
            optional: sets the template path to a specific path
    """

    def __init__(self, model_name, model_type, template_path=None):
        dir_this = os.path.dirname(__file__)
        par_dir = os.path.split(dir_this)[0]

        self.rigorous = False #Attribute for overwriting all templates

        self.template_directory = os.path.join(
            par_dir, "data", "templates"
        )  # Define Template directory
        supported_types = ["Supply", "Demand", "Pipe"]
        
        if model_type not in supported_types:
            raise ValueError(f"Model type {model_type} not supported. Choose from {supported_types}")
        
        self.model_name = model_name  # Component name
        self.model_type = model_type  # Component type

        self.version_info = get_versioning_info()  # Get versioning information

        self.optional_params = []  # List of optional parameters
        self.mandatory_params = []  # List of mandatory parameters
        try:
            self.template_name = self.model_name.replace(".", "_") + ".mako"
        except AttributeError:
            raise ValueError(f"No model name given! model_name: {model_name}, model_type: {model_type}, template_path: {template_path}")
        # check if template_path is filled and individual path should be used
        if template_path is None:
            if self.model_type == "Demand":
                self.save_path = os.path.join(
                    self.template_directory, "network", "demand", self.template_name
                )
            elif self.model_type == "Supply":
                self.save_path = os.path.join(
                    self.template_directory, "network", "supply", self.template_name
                )
            elif self.model_type == "Pipe":
                self.save_path = os.path.join(
                    self.template_directory, "network", "pipe", self.template_name
                )
            else:
                self.save_path = ""
        # set individual template path
        else:
            if not os.path.isabs(template_path):
                raise ValueError(f"Using custom templates requires absolutepath. You provided: {template_path}")

            # Prüfe, ob der Pfad mit .mako endet
            if not template_path.endswith('.mako'):
                raise ValueError(f"Absolute Template path must end with .mako extension: {template_path}")
            self.save_path = os.path.abspath(template_path)

    

    def _check_template(self):
        """Checks if selected template exists"""
        # Check if template path exists
        if not os.path.isfile(self.save_path):
            raise FileNotFoundError(f"No template found for model {self.model_name} at {self.save_path} with model type {self.model_type} and directory. Try to give absolute path")

    def call_function(self, function_string):
        """Calls function in template
            Attributes
            ----------
            function_string : str
                Name of the function in the .mako file.
        """
        self._check_template()
        template = Template(filename=self.save_path)
        re = template.get_def(function_string).render().split()
        return re

    def generate_new_template(self, path_library):
        """Generates a new template based on parameter and package information
        of the given class
        Parameters
        ----------

        path_library : str / list of strings
            Path to package.mo of the used library (e.g. C:\\...\\Aixlib\\package.mo)
            or list of paths to multiple used libraries
        """
        
        self.logger = set_up_logger("Uesgraph", level=logging.DEBUG) #Log file stored in the temp directory. Regard also console output
        self.logger.info("Uesgraph Version: %s", self.version_info["uesgraphs_version"])
        
        #1. Create ModelInfoExtractor object which opens a specified library (e.g AixLib) with an openmodelica session
        extractor = ModelInfoExtractor(path_library,log_level=10) #log_level=10 for debug, 20 for info. Log files are temporary stored in the temp directory. Regard also console output
        #2. Extract model information from the given class/component
        template_dict = extractor.extract_model_info(self.model_name) #Extracts parameters, connectors and packages and structures them in a dictionary

        #3. Generate Template string based on the extracted information
        template_str = self._generate_template_string(template_dict)
        self.logger.debug(f"")
        #4. Save created Template to mako file
        self._save_to_mako(template_str)
        return
       
    def _generate_template_string(self, template_dict):
        """
        Generates a template string for a Modelica component based on the provided template dictionary.

        This method creates a formatted string representation of a Modelica component,
        including its declaration, packages, parameters, annotations, and connections.

        Parameters:
        -----------
        template_dict : dict
            A dictionary containing the template information, with the following keys:
            - "Packages": List of required packages
            - "Parameters": Dictionary of parameter definitions for the component
            - "Connectors": Dictionary of the component's connectors

        Returns:
        --------
        str
            A formatted string representing the Modelica component template.

        Notes:
        ------
        - The method generates a template for a specific model type and name,
        which are assumed to be class attributes (self.model_type and self.model_name).
        - The template includes:
            1. Component declaration
            2. Package imports (using __generate_package_string)
            3. Parameter definitions (using __generate_parameter_string)
            4. Placement annotation (with configurable position)
            5. Real input connections (using __generate_real_input_string)
            6. Closing statements and parameter definitions (using __generate_end_string)
        - The generated template string is logged at the debug level.
        - The x and y coordinates in the placement annotation are rounded to 4 decimal places.
        - The method populates class attributes for mandatory and optional parameters,
        and connector lists, which are used in the end string generation.

        Example Output:
        ---------------
        The generated string will have a structure similar to:

            ModelName modelType${str(name)}(
                // Package imports
                // Parameter definitions
            )
            annotation(Placement(transformation(
            extent={{-2,-2},{2,2}},
            rotation=0,
            origin={x,y})));
            // Real input connections
            // Closing statements and parameter definitions
        """
        print(f"Generate new {self.model_type} template of model {self.model_name}")

        template_str = self.__generate_template_header()  # Generate header with version info and timestamp  
        template_str = template_str + f"  {self.model_name} {self.model_type.lower()}${{str(name)}}(\n"
        
        template_str = template_str + self.__generate_package_string(template_dict["Packages"])
        template_str = template_str + self.__generate_parameter_string(template_dict["Parameters"])
        
        # Write annotation
        template_str = (
            template_str + "    )\n"
            "    annotation(Placement(transformation(\n"
            "      extent={{-2,-2},{2,2}},\n"
            "      rotation=0,\n"
            "      origin={${str(round(x, 4))},${str(round(y, 4))}})));\n"
        )
        
        template_str = template_str + self.__generate_real_input_string(template_dict["Connectors"])
        template_str = template_str + self.__generate_end_string()
        self.logger.debug(f"Generated Template string: {template_str}")
        
        return template_str
    
    def __generate_template_header(self):
        ues_version = self.version_info["uesgraphs_version"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""// Generated by uesgraphs version {ues_version} on {timestamp}\n"""
    
    def __generate_package_string(self, packages):
        package_str = ""
        for package in set(packages):
            package_str = package_str + str(
                f"    redeclare package {package} = {package},\n")
        return package_str

    def __generate_parameter_string(self, parameters):
        """
        Generates a string for parameter definitions in the Modelica component.

        Parameters:
        -----------
        parameters : dict
            A dictionary of parameters, where keys are parameter names and
            values are Parameter objects (see also Parameter class below).

        Returns:
        --------
        str
            A formatted string of parameter definitions.

        Notes:
        ------
        - Parameters are sorted with optional parameters first.
        - Boolean parameters are handled differently from other types.
        - Optional parameters are wrapped in Mako conditional statements.
        - The method populates self.optional_params and self.mandatory_params.
        - The last parameter's trailing comma is removed.
        - Parameter processing is logged at the debug level.
        """

        parameters = dict(sorted(parameters.items(), key=lambda x: x[1].category != "optional")) #Sort for optional first then mandatory, necessary to erase the last comma
        param_strings = [] #Use a list of strings rather than a string is more performant
        for modelica_name, parameter in parameters.items():
            python_name = check_variable_name(modelica_name)
            if parameter.type == "Boolean":
                param_str = f"{modelica_name} = ${{str({python_name}).lower()}}"
            else:
                param_str = f"{modelica_name} = ${{str(round({python_name}, 4))}}"
            if parameter.category == "optional":
                param_strings.append(f"    %if {python_name} is not None:\n"
                        f"    {param_str},\n"
                        f"    %endif\n")
                self.optional_params.append(python_name)
            else:
                param_strings.append(f"    {param_str},\n")
                self.mandatory_params.append(python_name)
            self.logger.debug(f"Wrote parameter {modelica_name} as:\n {parameter.category} parameter")
        param_strings[-1] = param_strings[-1].rstrip(',\n') + '\n'
        return ''.join(param_strings)
    
    def __generate_real_input_string(self, connectors):
        """
        Generates a string for RealInput connectors in the Modelica component.

        Parameters:
        -----------
        connectors : dict
            A dictionary of connectors, where keys are connector names and
            values are Connector objects.

        Returns:
        --------
        str
            A formatted string of RealInput connector definitions.

        Notes:
        ------
        - Only processes connectors of type "Modelica.Blocks.Interfaces.RealInput".
        - Calculates positions for connectors in both the diagram and icon layers.
        - The method populates self.connector_list.
        - Connector additions are logged at the debug level.
        """
        self.connector_list = []  # List of connectors
        input_strings = []
        for connector_name, connector in connectors.items():
            if connector.type == "Modelica.Blocks.Interfaces.RealInput":
                number_connectors = len(self.connector_list)
                y_mod_t = str(25 - number_connectors * 10)
                y_mod_it = str(number_connectors * 10)
                origin_x = "-100" if self.model_type == "Demand" else "100"
                input_strings.append(
                    "\n  Modelica.Blocks.Interfaces.RealInput ${str(name + '%s')}\n"
                    "    annotation(Placement(\n"
                    "      transformation(\n"
                    "        extent={{-2,-2},{2,2}},\n"
                    "        rotation=0,\n"
                    "        origin={${str(round(x+25, 4))},${str(round(y+%s, 4))}}),\n"
                    "      iconTransformation(\n"
                    "        extent={{-2,-2},{2,2}},\n"
                    "        rotation=0,\n"
                    "        origin={${%s},${str(round(90 - i*180/(max(number_of_instances-1.0, 1.0)) + %s, 4))}})\n"
                    "      ));\n" % (connector_name, y_mod_t, origin_x, y_mod_it)
                )
                self.connector_list.append(connector_name)
        self.logger.debug(f"Added Real Inputs: {self.connector_list}")
        self.logger.debug(f"Real Input String: {input_strings}")
        return ''.join(input_strings)
    
    def __generate_end_string(self):
        """
        Generates the closing string for the Modelica component template.

        Returns:
        --------
        str
            A formatted string containing Mako definitions for main parameters,
            auxiliary parameters, and connector names.

        Notes:
        ------
        - Uses class attributes self.mandatory_params, self.optional_params,
        and self.connector_list populated by other methods.
        - Creates three Mako definitions:
        1. get_main_parameters(): for mandatory parameters
        2. get_aux_parameters(): for optional parameters
        3. get_connector_names(): for connector names
        """
        mandatory_str = " ".join(self.mandatory_params)
        mandatory_str = (    
            '<%def name="get_main_parameters()">\n'
            f"   {mandatory_str}\n"
            "</%def>"
        )
             
        optional_str = " ".join(self.optional_params)
        optional_str = (    
            '<%def name="get_aux_parameters()">\n'
            f"   {optional_str}\n"
            "</%def>"
        )

        connectors_str = " ".join(self.connector_list)
        connectors_str = (    
            '<%def name="get_connector_names()">\n'
            f"   {connectors_str}\n"
            "</%def>"
        )
        end_str = mandatory_str + optional_str + connectors_str
        return end_str 

    def _save_to_mako(self, template_str):
        if os.path.isfile(self.save_path) and self.rigorous == False:
            print(
                "Template for class %s already exists. Do you want to replace it"
                " with new template? Please enter"
                ' "Y" to proceed or "N" to abort.' % self.model_name
            )
            while True:
                choice = input()
                if choice == "Y":
                    print("Delete existing template for %s." % self.model_name)
                    os.remove(self.save_path)
                    break
                elif choice == "N":
                    print("Keep existing template.")
                    break
                else:
                    sys.stdout.write("Please respond with 'Y' or 'N'")

        if not os.path.isfile(self.save_path) or self.rigorous == True:
            print(
                "Write template for %s %s to %s"
                % (self.model_type, self.model_name, self.save_path)
            )
            with open(self.save_path, "w+") as text_file:
                text_file.write(template_str)
        return
        
    def render(self, node_data, i=None, number_of_instances=None, package_name=None):
        """Write Modelica code for Demands.OpenLoop.HeatPumpCarnot

        Parameters
        ----------
        node_data: dict
            information of systemmodel node
        i : int
            Counter of instances
        number_of_instances : int
            Number of total nodes of this type in graph

        Returns
        -------
        mo : str
            Rendered Modelica code
        """
        self._check_template()
        # Load .mako template
        template = Template(filename=self.save_path, strict_undefined=True)
        # Create parameters dict
        write_params = {}
        # Assert for main parameters
        main_params = template.get_def("get_main_parameters").render().split()
        # check if name is given as parameter
        assert "name" in node_data, "No name given!"
        main_params.append("name")
 
        for var in main_params:
            msg = "For the component model {}, {} must be given for node ({})".format(
                self.model_name, var, node_data["name"]
            )
            assert var in node_data, msg
            write_params[var] = node_data[var]

        # Check for auxiliary parameters
        aux_params = template.get_def("get_aux_parameters").render().split()
        for var in aux_params:
            if var in node_data:
                write_params[var] = node_data[var]
            else:
                write_params[var] = None

        # Add position info
        write_params["x"] = node_data["position"].x
        write_params["y"] = node_data["position"].y
        if "rotation" in node_data.keys():
            write_params["rotation"] = node_data["rotation"]
        # Add information about enumerations
        if i is not None:
            write_params["i"] = i
        if number_of_instances is not None:
            write_params["number_of_instances"] = number_of_instances

        write_params["package_name"] = package_name

        # TODO care about dhw
        # if "dhw" in self.nodes[node]['name']:
        #     gain_input = max(self.nodes[node]['input_heat'])
        # else:
        #     gain_input = 1

        mo = template.render_unicode(**write_params)

        return mo


import logging
from typing import Any, Dict, List, NamedTuple, Set

class Parameter(NamedTuple):
    """
    A named tuple representing a modelica parameter.

    Attributes:
        value (Any): The value of the parameter.
        type (str): The type of the parameter in model. Like Modelica.Units.SI.SpecificHeatCapacity or Boolean
        category (str, optional): The category of the parameter. 
            Either "optional" or "mandatory". Specified in _extract_parameters. Important for the template generation.
        description (str, optional): A brief description of the parameter. Defaults to "". Not needed yet.
        unit (str, optional): The unit of measurement for the parameter. Defaults to "". Not needed yet.

    Example:
        >>> param = Parameter(value=42, type="Integer", category="mandatory", 
        ...                   description="The answer to life, the universe, and everything", 
        ...                   unit="")
        >>> print(param.value)
        42
        >>> print(param.category)
        mandatory
    """
    value: Any
    type: str
    category: str = "" #Either optional or mandatory
    description: str = ""
    unit: str = ""
    

class Connector(NamedTuple):
    type: str

class ModelInfoExtractor:
    """
    A class to extract model information from OpenModelica classes.
    """
    def __init__(self, path_library: str, log_level: int = logging.INFO):
        self.logger = set_up_logger("ModelInfoExtractor", level=log_level)
        self.omc = self._open_omc_session(path_library)

    
    def _open_omc_session(self,path_library: str):
        """
        Opens an OpenModelica session and loads the specified library.

        This method initializes an OpenModelica session using OMPython and loads
        the Modelica library specified by the path_library parameter. It handles
        both single path strings and lists of paths.

        Parameters:
        -----------
        path_library : str or list of str
            The path(s) to the Modelica library file(s) to be loaded.

        Returns:
        --------
        OMCSessionZMQ
            An initialized OpenModelica session object with the specified library loaded.

        Raises:
        -------
        ImportError
            If the OMPython package is not installed.
        FileNotFoundError
            If the specified library file does not exist.
        Exception
            If the library fails to load for any reason.

        Notes:
        ------
        - This method requires the OMPython package and OpenModelica to be installed.
        - The method converts all paths to absolute paths and replaces backslashes with forward slashes.
        - It logs information about the loading process and any errors that occur.
        """
        # import OpenModelica Session
        try:
            from OMPython import OMCSessionZMQ
        except ImportError:
            raise ImportError(
                "For automated template generation you need to install the "
                "OMPython package"
                " and Openmodelica"
            )
        if not isinstance(path_library, list):
            path_library = [path_library]

        omc = OMCSessionZMQ()
        ## Load Library (e.g. Aixlib)
        self.logger.info(f"Libraries to load: {path_library}")
        for path in path_library:
            self.logger.info(f"Load Library: {path}")
            abs_path = os.path.abspath(path).replace("\\", "/")
            if os.path.exists(abs_path)!= True:
                fail_msg = (f"The file does not exist: {abs_path}")
                self.logger.error(fail_msg)
                raise FileNotFoundError(fail_msg)
            success = omc.loadFile((abs_path))
            if success != "true\n":
                error = omc.sendExpression("getErrorString()")
                self.logger.error(error)
                raise Exception("Could not load " + abs_path + "  " + error)         
        return omc
    
    def list_main_models(self): #Work in progress
        """
        Lists all main models in the loaded library.

        This method queries OpenModelica for a list of all main models in the currently loaded library.
        It returns a list of class names that can be used for further analysis.

        Returns:
        --------
        List[str]
            A list of class names representing the main models in the loaded library.

        Notes:
        ------
        - The method logs debug information about the found classes.
        """
        raise NotImplementedError("Method not implemented yet. TODO: Get hierarchy of classes")
    
        # Erste Ebene
        all_classes = self.omc.sendExpression('getClassNames()')
        print("Erste Ebene:", all_classes)  # ('ModelicaServices', 'Complex', 'Modelica', 'AixLib')

        # Zweite Ebene - AixLib Pakete
        aixlib_classes = self.omc.sendExpression('getClassNames(AixLib, recursive=false)')
        print("AixLib Pakete:", aixlib_classes)

        # Dritte Ebene - für jedes AixLib Paket
        for class_name in aixlib_classes:
            full_name = f"AixLib.{class_name}"  # Wichtig: Vollständiger Pfad!
            class_info = self.omc.sendExpression(f'getClassInformation({full_name})')
            print(f"\nKlasse: {class_name}")
            print(f"Info: {class_info}")
            
            # Unterklassen des Pakets
            sub_classes = self.omc.sendExpression(f"getClassNames({full_name}, recursive=false)")
            print(f"Unterklassen: {sub_classes}")
        
        return None


    def extract_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Extracts parameters, connectors and packages from OpenModelica-classes.

        Args:
            model_name: Liste der zu untersuchenden Klassennamen

        Returns:
            Dictionary mit extrahierten Informationen (Parameters, Connectors, Packages)
        """
        template_dict: Dict[str, Any] = {"Parameters": {}, "Connectors": {}, "Packages": set()}
        
        try:
            class_names = self._get_inherited_classes(model_name)
            for name in class_names:
                template_dict["Parameters"].update(self._extract_parameters(name))
                template_dict["Connectors"].update(self._extract_connectors(name))
                template_dict["Packages"].update(self._extract_packages(name))
        except Exception as e:
            self.logger.error(f"Unexpected error during extraction: {e}")
        finally:
            self._close_omc_session()
        self.logger.debug(f"Extracted information: {template_dict}")
        return template_dict

    def _get_inherited_classes(self,model_name) -> List[str]:
        """
        Determines all inherited classes of the given model.

        This method retrieves the inheritance hierarchy for a specified Modelica model.
        For example, the class 'AixLib.Fluid.DistrictHeatingCooling.Pipes.DHCPipe' 
        inherits from classes like 'AixLib.Fluid.Interfaces.PartialTwoPortInterface' 
        and 'AixLib.Fluid.Interfaces.PartialTwoPort'.

        Parameters:
        -----------
        model_name : str
            The name of the Modelica model to analyze.

        Returns:
        --------
        List[str]
            A list of class names, including the main model and all inherited classes,
            in order of inheritance (from child to parent).

        Raises:
        -------
        AssertionError
            If the provided model_name is not a valid Modelica model.
        Exception
            If the class inherits from more than one class, which is not expected
            in this implementation.

        Notes:
        ------
        - The method uses OpenModelica's OMPython API to query model information.
        - It assumes single inheritance and will raise an exception for multiple inheritance.
        - The method logs debug information about the found classes.
        """
        class_names = [model_name]
        msg = f"{class_names[-1]} is not a model"
        assert self.omc.sendExpression(f"isModel({class_names[-1]})"), msg

        while True:
            inherited_class = self.omc.sendExpression(f"getInheritedClasses({class_names[-1]})")
            if len(inherited_class) == 0:
                break  # Break loop, beacause no more inherited class is present
            elif len(inherited_class) == 1:
                class_names.append(inherited_class[0])
            else:
                raise Exception("Class inherited from more than one class.")

        self.logger.debug(f"Found following classes (including inherited): {class_names}")
        return class_names

    def _extract_parameters(self, name: str) -> dict:
        """
        Extracts all parameters from a given Modelica model or component.

        This method retrieves and processes all parameters of the specified model or component,
        categorizing them as either mandatory or optional based on their value assignment.

        Parameters:
        -----------
        name : str
            The name of the Modelica model or component to analyze.

        Returns:
        --------
        dict
            A dictionary where keys are parameter names and values are Parameter objects.
            Each Parameter object contains information such as value, type, category,
            description, and unit.

        Notes:
        ------
        - Parameters are considered mandatory if they have no assigned value, except for 'm_flow_nominal'.
        - The method uses OpenModelica's OMPython API to query model information.
        - Errors during parameter extraction are logged but do not halt the process.
        - The extracted parameters are logged at the debug level.

        Parameter Object Structure:
        ---------------------------
        Each Parameter object in the returned dictionary has the following attributes:
        - value: The assigned value of the parameter (empty string if not assigned)
        - type: The Modelica class of the parameter
        - category: Either "mandatory" or "optional"
        - description: The comment associated with the parameter (if any)
        - unit: The unit of the parameter (if specified)

        Raises:
        -------
        No specific exceptions are raised, but errors during parameter extraction
        are caught and logged.
        """
        parameters = {}
        components = self.omc.sendExpression(f"getComponentsTest({name})")
        for comp in components:
            if comp["variability"] == "parameter":
                try:
                    val = self.omc.sendExpression(f"getComponentModifierValue({name},{comp['name']})")
                    if val == "" and not comp["name"] == "m_flow_nominal":
                        category = "mandatory"
                    else:
                        category = "optional"
                    parameters[comp["name"]] = Parameter(
                        value=val,
                        type=comp["className"],
                        category=category,
                        description=comp.get("comment", ""),
                        unit=comp.get("unit", "")
                    )
                except Exception as e:
                    self.logger.error(f"Error extracting parameter {comp['name']} from {name}: {e}")
        self.logger.debug(f"Found following Parameters: {parameters}")
        return parameters
    
    def _extract_connectors(self, name: str) -> dict:
        connectors = {}
        components = self.omc.sendExpression(f"getComponentsTest({name})")
        for comp in components:
            if self.omc.sendExpression(f"isConnector({comp['className']})"):
                connectors[comp["name"]] = Connector(
                    type=comp["className"]
                    )
        self.logger.debug(f"Found following Connectors: {connectors}")
        return connectors

    def _extract_packages(self, name: str):
        packages = self.omc.sendExpression(f"getPackages({name})")
        self.logger.debug(f"Found following Packages: {packages}")
        return packages
    
    def _close_omc_session(self) -> None:
        try:
            self.omc.sendExpression("quit()")
            self.logger.info("OMC session closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing OMC session: {e}")