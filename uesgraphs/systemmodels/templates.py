# -*- coding: utf-8 -*-
"""
This module includes the UESModel graph to write Modelica code from uesgraphs
"""

import os
import sys
from mako.template import Template

versionfile = os.path.join(os.path.dirname(__file__), "version.py")

exec(open(versionfile).read())


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
        self.template_directory = os.path.join(
            par_dir, "data", "templates"
        )  # Define Template directory
        self.model_name = model_name  # Component name
        self.model_type = model_type  # Component type
        self.template_name = self.model_name.replace(".", "_") + ".mako"
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
            self.save_path = os.path.abspath(template_path)

    def _check_template(self):
        """Checks if selected template exists"""
        # Check if template path exists
        if not os.path.isfile(self.save_path):
            exit(
                "No template found for model %s at %s"
                % (self.model_name, self.save_path)
            )

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
        if not isinstance(path_library, list):
            path_library = [path_library]
        assert self.model_type in [
            "Demand",
            "Supply",
            "Pipe",
        ], "Choose model Type from Demand, Supply, Pipe for template generation"

        # import OpenModelica Session
        try:
            from OMPython import OMCSessionZMQ
        except ImportError:
            exit(
                "For automated template generation you need to install the "
                "OMPython package"
                " and Openmodelica"
            )

        omc = OMCSessionZMQ()
        # Load Library (e.g. Aixlib)
        for lib in path_library:
            success = omc.loadFile(filename=os.path.abspath(lib))
            # if not success:
            if success != "true\n":
                raise Exception("Could not load " + lib)

        # create list with file and all inherited files
        class_names = [self.model_name]
        msg = "%s is not a model" % class_names[-1]
        assert omc.sendExpression("isModel(" + class_names[-1] + ")"), msg
        while True:
            inherited_class = omc.sendExpression(
                "getInheritedClasses(" + class_names[-1] + ")"
            )
            if len(inherited_class) == 0:
                break  # Break loop, beacause no more inherited class is present
            elif len(inherited_class) == 1:
                class_names.append(inherited_class[0])
            else:
                raise Exception("Class inherited from more than one class.")

        # Get parameter, packages and connectors of all classes
        template_dict = {"Parameters": [], "Connectors": [], "Packages": []}
        for name in class_names:
            # Check for parameters
            parameters = omc.sendExpression("getParameterNames(" + name + ")")
            for param in parameters:
                val = omc.sendExpression(
                    "getComponentModifierValue(" + name + "," + param + ")"
                )
                template_dict["Parameters"].append([param, val])
            # Check for Inputs
            components = omc.sendExpression("getComponents(" + name + ")")
            for comp in components:
                if omc.sendExpression("isConnector(" + comp[0] + ")"):
                    con_name = comp[1]
                    type = comp[0]
                    template_dict["Connectors"].append([con_name, type])
            # Check for packages
            packages = omc.sendExpression("getPackages(" + name + ")")
            for package in packages:
                template_dict["Packages"].append(package)

        # Close omc session
        omc.sendExpression("quit()")

        # generate Template
        if self.model_type == "Demand":
            print("Generate new Demand template of model " + self.model_name)
            # write Demand model name
            template_str = str("  " + self.model_name + " demand${str(name)}(\n")
        elif self.model_type == "Supply":
            print("Generate new Supply template of model " + self.model_name)
            # write Supply model name
            template_str = str("  " + self.model_name + " supply${str(name)}(\n")
        elif self.model_type == "Pipe":
            print("Generate new Pipe template of model " + self.model_name)
            # write Pipe model name
            template_str = str("  " + self.model_name + " pipe${str(name)}(\n")

        # write packages
        for package_name in set(
            template_dict["Packages"]
        ):  # set() command automatically erases duplicates
            template_str = template_str + str(
                "    redeclare package %s = %s,\n" % (package_name, package_name)
            )
        # write parameters
        mandatory_params = []  # list of parameters where value needs to be given
        optional_params = []  # list of parameters where default value is given
        for parameter in template_dict["Parameters"]:
            parameter_name = parameter[0]
            parameter_val = parameter[1]
            # Order Parameters into mandatory and optional parameters
            # TODO m_flow_nominal is an exception
            if parameter_val == "" and not parameter_name == "m_flow_nominal":
                # Definition without default value for parameter
                mandatory_params.append(parameter_name)
            else:
                # Definition with default value for parameter
                optional_params.append(parameter_name)
        # Write optional parameters first
        for parameter_name in optional_params:
            template_str = template_str + str(
                "    %%if %s is not None:\n"
                "    %s = ${str(round(%s, 4))},\n"
                "    %%endif\n" % (parameter_name, parameter_name, parameter_name)
            )
        # Write mandatory parameters second
        for parameter_name in mandatory_params:
            if parameter_name == mandatory_params[-1]:
                # don't write last comma for last parameter
                template_str = template_str + str(
                    "    %s = ${str(round(%s, 4))}\n" % (parameter_name, parameter_name)
                )
            else:
                template_str = template_str + str(
                    "    %s = ${str(round(%s, 4))},\n"
                    % (parameter_name, parameter_name)
                )

        # write annotation
        template_str = (
            template_str + "    )\n"
            "    annotation(Placement(transformation(\n"
            "      extent={{-2,-2},{2,2}},\n"
            "      rotation=0,\n"
            "      origin={${str(round(x, 4))},${str(round(y, 4))}})));\n"
        )

        # Add Real Inputs
        connector_list = []  # List of connectors
        for connector in template_dict["Connectors"]:
            connector_name = connector[0]
            connector_type = connector[1]
            if connector_type == "Modelica.Blocks.Interfaces.RealInput":
                y_mod_t = str(25 - len(connector_list) * 10)
                y_mod_it = str(len(connector_list) * 10)
                if self.model_type == "Demand":
                    origin_x = "str(-100)"
                elif self.model_type == "Supply":
                    origin_x = "str(100)"
                template_str = (
                    template_str
                    + "\n  Modelica.Blocks.Interfaces.RealInput ${str(name + '%s')}\n"
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
                connector_list.append(connector_name)

        # Add function to return list of parameters
        # NOTE: In a first draft I added a newline command in front of every function.
        # This improves readability of the.mako-File but adds a blank line in the final
        # modelica model. Old string looked like: '\n<%def ...></%def>'
        temp_str = " ".join(mandatory_params)
        template_str = (
            template_str + '<%def name="get_main_parameters()">\n'
            "   " + temp_str + "\n"
            "</%def>"
        )
        temp_str = " ".join(optional_params)
        template_str = (
            template_str + '<%def name="get_aux_parameters()">\n'
            "   " + temp_str + "\n"
            "</%def>"
        )
        temp_str = " ".join(connector_list)
        template_str = (
            template_str + '<%def name="get_connector_names()">\n'
            "   " + temp_str + "\n"
            "</%def>"
        )

        # Save template
        if os.path.isfile(self.save_path):
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

        if not os.path.isfile(self.save_path):
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
