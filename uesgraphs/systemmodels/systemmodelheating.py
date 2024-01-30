"""
This module includes the UESModel graph to write Modelica code from uesgraphs
"""

import datetime
from functools import partial
from mako.template import Template
import os
import pyproj
import shapely
import shapely.geometry as sg
import shapely.ops as ops
import sys
import warnings
import json

from uesgraphs.uesgraph import UESGraph
from uesgraphs.systemmodels.templates import UESTemplates


versionfile = os.path.join(os.path.dirname(__file__), "version.py")

exec(open(versionfile).read())


class SystemModelHeating(UESGraph):
    """Writes Modelica code for system models from uesgraphs information

    While a uesgraph object uses edges to describe pipe connections between
    nodes, the Modelica model needs a specific node representing the pipe
    model and connections between connectors of each model. Therefore, UESModel
    initializes a new graph object from information of an uesgraph object.
    At the current stage, the uesgraph object should be a subgraph that only
    contains one network.

    Parameters
    ----------
    model_name : str
    Name of the model, will be used for naming components and output file

    Attributes
    ----------
    nodelist_pipe : list
        List of all pipe node numbers in the graph
    network_type : {'heating'}
        Type of network to be modeled
    stop_time : float
        Stop time for simulation in seconds
    timestep : float
        Timestep for simulation in seconds
    time : list
        time vector calculated from 'timestep' and 'stop_time'
    solver : str
        Solver for use in Dymola
    medium : str
        Default is 'water'
    doc_string : str
        A doc string for the Modelica mode
    documentation : str
        Currently just a string that will be written to the model documentation
    add_ground_around_pipe : boolean
        For True, the ground around the pipe will be modeled by an RC network. This requires values
        for `RExt`, `RExtRem`, `CExt`, `T_ground_start`, and `n` for each edge to parameterize a
        model using
        `AixLib.ThermalZones.ReducedOrder.RC.BaseClasses.ExteriorWall` for the ground
    uses : list
        A list of string specifying all used Modelica libraries
    control_pressure : dict
        Collection of settings for pressure control: `building`, `dp`, `supply`
    """

    def __init__(self, model_name="Test", network_type="heating"):
        """Construct SystemModelHeating class."""
        # The super() is necessary to also execute nx.graphs's init
        super(SystemModelHeating, self).__init__()

        self.meta_data = {}

        self.model_name = model_name
        self.nodelist_pipe = []
        self.network_type = network_type

        self.stop_time = None
        self.timestep = None
        self.__time = []
        self.solver = "Cvode"

        self.__medium = "AixLib.Media.Water"

        self.__doc_string = None
        self.documentation = "Network model generated with uesmodels"
        self.uses = ["AixLib"]

        self.add_ground_around_pipe = False
        self.control_pressure = {}

        self.graph["T_ground"] = [273.15 + 10]  # Default ground temperature

        self.with_heat_flow_output = False
        self.with_heat_loss_output = False

        dir_this = os.path.dirname(__file__)
        dir_par = os.path.split(dir_this)[0]
        self.template_directory = os.path.join(dir_par, "data", "templates")
        self.templates = {
            # Ground temperature
            "t_ground_table": {"render": self._write_mo_t_ground_table},
            "t_ground_kusuda": {"render": self._write_mo_t_ground_kusuda},
        }

    @property
    def time(self):
        if self.stop_time is not None and self.timestep is not None:
            number_of_timesteps = int((self.stop_time / self.timestep) + 1)
            self.__time = [x * self.timestep for x in range(number_of_timesteps)]
        return self.__time

    @property
    def doc_string(self):
        if self.__doc_string is None:
            output = "Model automatically generated with uesmodels at {}"
            output_dated = output.format(datetime.datetime.now())
            return output_dated
        else:
            return self.__doc_string

    @doc_string.setter
    def doc_string(self, value):
        if len(value) > 76:
            raise ValueError("Doc-string should not be longer than 76 chars")
        self.__doc_string = value

    @property
    def medium(self):
        return self.__medium

    @medium.setter
    def medium(self, value):
        if value not in [
            "AixLib.Media.Water",
            "AixLib.Media.Specialized.Water.ConstantProperties_pT",
            "AixLib.Media.Antifreeze.PropyleneGlycolWater",
        ]:
            raise ValueError("Unknown Medium choice")
        self.__medium = value

    def import_nodes_from_uesgraph(self, uesgraph_input):
        """Adds uesgraph_input's nodes to the model graph

        As a first step for the conversion from a uesgraph to a uesmodel graph,
        this method imports the uesgraph's nodes to the nodes of
        this class. The method conserves each node's attributes, but converts
        the x and y coordinates from GIS data to coordinates on the canvas
        for graphical representation of the Modelica model.

        Parameters
        ----------
        uesgraph_input : uesgraphs.uesgraph.UESGraph object
            At current stage, this uesgraph should contain only 1 network of 1
            type that is indexed in the corrsponding nodelist as `'default'`
        """

        def _transform_coords(gis_position):
            """Transforms coords from GIS to coords on Modelica canvas

            Parameters
            ----------
            gis_position : shapely.geometry.Point object
                Point object with coords from GIS

            Returns
            -------
            modelica_position : shapely.geometry.Point object
                Point object with coords on Modelica canvas
            """
            # Transform coordinates to plane
            modelica_position = ops.transform(
                partial(
                    pyproj.transform,
                    pyproj.Proj(init="EPSG:4326"),
                    pyproj.Proj(
                        proj="aea",
                        lat1=uesgraph_input.min_position.y,
                        lat2=uesgraph_input.max_position.y,
                    ),
                ),
                gis_position,
            )
            # Transform the minimum position to the same plane
            new_min = ops.transform(
                partial(
                    pyproj.transform,
                    pyproj.Proj(init="EPSG:4326"),
                    pyproj.Proj(
                        proj="aea",
                        lat1=uesgraph_input.min_position.y,
                        lat2=uesgraph_input.max_position.y,
                    ),
                ),
                uesgraph_input.min_position,
            )
            # Translate node, so that minimum position is at (0, 0)
            modelica_position = shapely.affinity.translate(
                modelica_position, xoff=-new_min.x, yoff=-new_min.y
            )
            return modelica_position

        for node in uesgraph_input.nodelist_building:
            # new_position = _transform_coords(uesgraph_input.node[
            #                                      node]['position'])
            new_position = uesgraph_input.node[node]["position"]

            name_node = uesgraph_input.node[node]["name"]
            if name_node[0].isdigit():
                name_node = self.model_name[0] + name_node

            bldg = self.add_building(
                name=name_node,
                position=new_position,
                is_supply_heating=uesgraph_input.node[node]["is_supply_heating"],
                is_supply_cooling=uesgraph_input.node[node]["is_supply_cooling"],
                is_supply_electricity=uesgraph_input.node[node][
                    "is_supply_electricity"
                ],
                is_supply_gas=uesgraph_input.node[node]["is_supply_gas"],
                is_supply_other=uesgraph_input.node[node]["is_supply_other"],
            )
            self.nodes[bldg]["has_table"] = False

            for attrib in uesgraph_input.node[node]:
                if attrib not in self.nodes[bldg]:
                    self.nodes[bldg][attrib] = uesgraph_input.node[node][attrib]

        for network_type in self.network_types:
            if network_type == "heating":
                nodelist = uesgraph_input.nodelists_heating["default"]
            elif network_type == "cooling":
                nodelist = uesgraph_input.nodelists_cooling["default"]
            elif network_type == "electricity":
                nodelist = uesgraph_input.nodelists_electricity["default"]
            elif network_type == "gas":
                nodelist = uesgraph_input.nodelists_gas["default"]
            elif network_type == "others":
                nodelist = uesgraph_input.nodelists_others["default"]
            else:
                raise ValueError("Unknown network type")

            for node in nodelist:
                # new_position = _transform_coords(uesgraph_input.node[
                #                                      node]['position'])
                new_position = uesgraph_input.node[node]["position"]
                new = self.add_network_node(
                    name=uesgraph_input.node[node]["name"],
                    network_type=network_type,
                    position=new_position,
                    check_overlap=False,
                )

                for attrib in uesgraph_input.node[node]:
                    if attrib not in self.nodes[new]:
                        self.nodes[new][attrib] = uesgraph_input.node[node][attrib]

    def add_pipe_node(self, name=None, position=None):
        """Adds a pipe node to the graph

        Parameters
        ----------
        name : str, int, or float
            A name for the building represented by this node. If None is given,
            the newly assigned node number will also be used as name.
        position : shapely.geometry.Point object
            New node's position

        Returns
        -------
        node_number : int
            Identifier of the newly created pipe node
        """
        node_number = self.new_node_number()
        if name is None:
            name = node_number

        self.add_node(node_number, name=name, node_type="pipe_heat", position=position)

        self.nodelist_pipe.append(node_number)

        self.nodes_by_name[name] = node_number

        return node_number

    def remove_pipe_node(self, node_number):
        """Removes the specified pipe node from the graph

        Parameters
        ----------
        node_number : int
            Identifier of the node in the graph
        """
        if node_number in self.nodelist_pipe:
            self.nodelist_pipe.remove(node_number)
            self.remove_node(node_number)
        else:
            warnings.warn(
                "Node number has not been found in pipe"
                + "nodelist. Therefore, node has not been removed."
            )

    def import_pipes_from_uesgraph(self, uesgraph_input):
        """Adds uesgraph_input's pipe edges as nodes to uesmodel graph

        The second step for conversion of a uesgraph to a uesmodel graph
        involves the conversion of pipes from edges to nodes of their own.
        They keep their attributes like length and diameter and in addition
        are assigned x and y coordinates which locate them in the middle
        between the nodes they originally connected. Furthermore, new edges are
        created representing the connection from the pipe model's ports to the
        next nodes.

        Parameters
        ----------
        uesgraph_input : uesgraphs.uesgraph.UESGraph object
            At current stage, this uesgraph should contain only 1 network of 1
            type that is indexed in the corresponding nodelist as `'default'`
        """
        for curr_edge in uesgraph_input.edges():
            # Find the edge's nodes' correct numbers via their name
            name_node_0 = uesgraph_input.node[curr_edge[0]]["name"]
            name_node_1 = uesgraph_input.node[curr_edge[1]]["name"]

            if curr_edge[0] in uesgraph_input.nodelist_building:
                if name_node_0[0].isdigit():
                    name_node_0 = self.model_name[0] + name_node_0
            if curr_edge[1] in uesgraph_input.nodelist_building:
                if name_node_1[0].isdigit():
                    name_node_1 = self.model_name[0] + name_node_1

            curr_edge_node_0 = self.nodes_by_name[name_node_0]
            curr_edge_node_1 = self.nodes_by_name[name_node_1]

            # Find position for new pipe node between both neighbors
            new_position = sg.LineString(
                [
                    uesgraph_input.node[curr_edge[0]]["position"],
                    uesgraph_input.node[curr_edge[1]]["position"],
                ]
            ).centroid

            # Create new pipe node and transfer attributes from former edge
            pipe_name = uesgraph_input.edges[curr_edge[0], curr_edge[1]]["name"]
            curr_pipe = self.add_pipe_node(position=new_position, name=pipe_name)
            self.nodes[curr_pipe]["length"] = uesgraph_input.edges[
                curr_edge[0], curr_edge[1]
            ]["length"]

            self.nodes[curr_pipe]["diameter"] = uesgraph_input.edges[
                curr_edge[0], curr_edge[1]
            ]["diameter"]

            for attrib in uesgraph_input.edges[curr_edge[0], curr_edge[1]]:
                if attrib not in self.nodes[curr_pipe]:
                    self.nodes[curr_pipe][attrib] = uesgraph_input.edges[
                        curr_edge[0], curr_edge[1]
                    ][attrib]

            # Rotation of each pipe model depending on the coordinates
            # of the connected nodes in degree
            self.nodes[curr_pipe]["rotation"] = self.calc_angle(
                self.nodes[curr_edge_node_0]["position"],
                self.nodes[curr_edge_node_1]["position"],
                output="degrees",
            )

            assert curr_edge_node_0 in self.nodes()
            assert curr_edge_node_1 in self.nodes()

            self.add_edge(curr_pipe, curr_edge_node_0)
            self.add_edge(curr_pipe, curr_edge_node_1)

    def import_from_uesgraph(self, uesgraph_input):
        """Imports nodes and edges from uesgraph and adds pipe nodes

        Parameters
        ----------

        uesgraph_input : uesgraphs.uesgraph.UESGraph object
            At current stage, this uesgraph should contain only 1 network of 1
            type that is indexed in the corresponding nodelist as `'default'`
        """
        self.import_nodes_from_uesgraph(uesgraph_input)
        self.import_pipes_from_uesgraph(uesgraph_input)

        # Import graph attributes
        for attrib in uesgraph_input.graph:
            self.graph[attrib] = uesgraph_input.graph[attrib]

    def set_connection(self, remove_network_nodes=True):
        """Sets connections between supplies, pipes and buildings

        To connect supplies, pipes, and buildings, each edge of the model graph
        is assigned four attributes ('con1', 'con2', 'con1R', 'con2R') that
        characterize the connected node (supply, pipe, building) and the used
        port of the node (port_a, port_b).
        In case the node is a supply, a pipe, or a building, the attribute
        (con1, con2, con1R, con2R) contains the corresponding Modelica-Code.
        In case the node is a network-node the attribute only contains
        the number of the node, since network-nodes can be connected to more
        then one node. The connections of the network-nodes is written later
        on in method 'write_network_model()'.

        For remove_network_nodes is True, ports depend on type of node:
                pipe    network    building    supply
        con1    a/b     node #        a          b
        con1R   a/b     node #        b          a
        con2    a/b     node #        a          b
        con2R   a/b     node #        b          a

        Parameters
        ----------
        remove_network_nodes : boolean
            If True, all connections at network nodes will be clustered onto
            connecting ports. If False, network nodes will get their own
            representation in the conncetion network.
        """
        if self.network_type == "heating":
            flag_supply = "is_supply_heating"
            nodelist = self.nodelists_heating["default"]
        elif self.network_type == "cooling":
            flag_supply = "is_supply_cooling"
            nodelist = self.nodelists_cooling["default"]
        else:
            raise RuntimeError("Unknown network type")

        clusters = {}
        for node in nodelist:
            clusters[node] = []
        for curr_edge in self.edges(data=True):
            for edge_node in curr_edge:
                if edge_node == curr_edge[0]:
                    other_node = curr_edge[1]
                else:
                    other_node = curr_edge[0]

                if edge_node in self.nodelist_building:
                    if self.nodes[edge_node][flag_supply] is False:
                        con = "demand" + str(self.nodes[edge_node]["name"]) + ".port_a"
                        con_R = (
                            "demand" + str(self.nodes[edge_node]["name"]) + ".port_b"
                        )
                    else:
                        con = "supply" + str(self.nodes[edge_node]["name"]) + ".port_b"
                        con_R = (
                            "supply" + str(self.nodes[edge_node]["name"]) + ".port_a"
                        )
                elif edge_node in nodelist:
                    con = edge_node
                    con_R = edge_node
                    if edge_node == curr_edge[0]:
                        clusters[edge_node].append(curr_edge[1])
                    elif edge_node == curr_edge[1]:
                        clusters[edge_node].append(curr_edge[0])
                elif edge_node in self.nodelist_pipe:
                    angle = self.calc_angle(
                        self.nodes[edge_node]["position"],
                        self.nodes[other_node]["position"],
                        output="degrees",
                    )
                    if abs(self.nodes[edge_node]["rotation"] - angle) < 90:
                        con = "pipe" + str(self.nodes[edge_node]["name"]) + ".port_b"
                        con_R = (
                            "pipe"
                            + str(self.nodes[edge_node]["name"])
                            + "R."
                            + "port_b"
                        )
                    else:
                        con = "pipe" + str(self.nodes[edge_node]["name"]) + ".port_a"
                        con_R = (
                            "pipe"
                            + str(self.nodes[edge_node]["name"])
                            + "R."
                            + "port_a"
                        )
                if edge_node == curr_edge[0]:
                    self.edges[curr_edge[0], curr_edge[1]]["con1"] = con
                    self.edges[curr_edge[0], curr_edge[1]]["con1R"] = con_R
                elif edge_node == curr_edge[1]:
                    self.edges[curr_edge[0], curr_edge[1]]["con2"] = con
                    self.edges[curr_edge[0], curr_edge[1]]["con2R"] = con_R

        if remove_network_nodes is True:
            for network_node in clusters:
                # Find port information of all nodes connected to network_node
                # and assign to 'fwd' and 'rtn' in ports dict
                ports = {}
                for curr_node in clusters[network_node]:
                    ports[curr_node] = {}
                    if self.edges[network_node, curr_node]["con1"] != network_node:
                        ports[curr_node]["fwd"] = self.edges[network_node, curr_node][
                            "con1"
                        ]
                        ports[curr_node]["rtn"] = self.edges[network_node, curr_node][
                            "con1R"
                        ]
                    else:
                        ports[curr_node]["fwd"] = self.edges[network_node, curr_node][
                            "con2"
                        ]
                        ports[curr_node]["rtn"] = self.edges[network_node, curr_node][
                            "con2R"
                        ]

                # Replace connections via network nodes with direct connections
                # between model nodes
                first_node = clusters[network_node][0]
                self.remove_edge(first_node, network_node)
                for curr_node in clusters[network_node][1:]:
                    self.add_edge(
                        first_node,
                        curr_node,
                        con1=ports[first_node]["fwd"],
                        con2=ports[curr_node]["fwd"],
                        con1R=ports[first_node]["rtn"],
                        con2R=ports[curr_node]["rtn"],
                    )
                self.remove_network_node(network_node)
        else:
            for network_node in clusters:
                if "name" not in self.nodes[network_node]:
                    self.nodes[network_node]["name"] = str(network_node)

                self.nodes[network_node]["degree"] = self.degree(network_node)

                for i, neighbor in enumerate(self.neighbors(network_node)):
                    curr_port = "junction{}.ports[{}]".format(
                        self.nodes[network_node]["name"], i
                    )
                    curr_port_R = "junction{}R.ports[{}]".format(
                        self.nodes[network_node]["name"], i
                    )
                    for con in self.edges[neighbor, network_node].keys():
                        con_element = self.edges[neighbor, network_node][con]
                        if con_element == network_node:
                            if "R" in con:
                                self.edges[neighbor, network_node][con] = curr_port_R
                            else:
                                self.edges[neighbor, network_node][con] = curr_port

        # If the IBPSA pipe approach is used (always, currently), overwrite the connect statements
        # to use the asymmetrical pipe setup
        if True:
            occurrences_port = {}
            for pipe in self.nodelist_pipe:
                occurrences_port[self.nodes[pipe]["name"]] = 0
            # Supply network
            for edge in self.edges():
                con1 = self.edges[edge[0], edge[1]]["con1"]
                con2 = self.edges[edge[0], edge[1]]["con2"]
                if "pipe" in con1:
                    name_pipe = con1.split(".")[0][4:]
                    if "port_b" in con1:
                        occurrences_port[name_pipe] += 1
                        con1_new = "pipe{}.ports_b[{}]".format(
                            name_pipe, occurrences_port[name_pipe]
                        )
                        self.edges[edge[0], edge[1]]["con1"] = con1_new
                if "pipe" in con2:
                    name_pipe = con2.split(".")[0][4:]
                    if "port_b" in con2:
                        occurrences_port[name_pipe] += 1
                        con2_new = "pipe{}.ports_b[{}]".format(
                            name_pipe, occurrences_port[name_pipe]
                        )
                        self.edges[edge[0], edge[1]]["con2"] = con2_new

            # Pipes
            for pipe in self.nodelist_pipe:
                self.nodes[pipe]["nPorts"] = max(
                    1, occurrences_port[self.nodes[pipe]["name"]]
                )

            # Return network
            occurrences_port = {}
            for pipe in self.nodelist_pipe:
                occurrences_port[self.nodes[pipe]["name"]] = 0
            for edge in self.edges():
                con1R = self.edges[edge[0], edge[1]]["con1R"]
                con2R = self.edges[edge[0], edge[1]]["con2R"]
                if "pipe" in con1R:
                    name_pipe = con1R.split(".")[0].replace("R", "")[4:]
                    if "port_b" in con1R:
                        occurrences_port[name_pipe] += 1
                        con1R_new = "pipe{}R.ports_b[{}]".format(
                            name_pipe, occurrences_port[name_pipe]
                        )
                        self.edges[edge[0], edge[1]]["con1R"] = con1R_new
                if "pipe" in con2R:
                    name_pipe = con2R.split(".")[0].replace("R", "")[4:]
                    if "port_b" in con2R:
                        occurrences_port[name_pipe] += 1
                        con2R_new = "pipe{}R.ports_b[{}]".format(
                            name_pipe, occurrences_port[name_pipe]
                        )
                        self.edges[edge[0], edge[1]]["con2R"] = con2R_new

    def write_medium_definition(self):
        """Write the rendered Modelica code for the Medium definition

        Returns
        -------
        mo_medium : str
            Rendered Modelica code for the medium definition
        """
        dir_templates_network = os.path.join(self.template_directory, "network")

        if self.medium == "AixLib.Media.Water":
            template_medium = Template(
                filename=os.path.join(
                    dir_templates_network, "medium", "AixLib_Media_Water.mako"
                )
            )
            mo_medium = template_medium.render_unicode(T_default=self.T_nominal)
        elif self.medium == "AixLib.Media.Specialized.Water." "ConstantProperties_pT":
            template_medium = Template(
                filename=os.path.join(
                    dir_templates_network,
                    "medium",
                    "Specialized_Water_ConstantProperties_pT.mako",
                )
            )
            mo_medium = template_medium.render_unicode(
                T_nominal=self.T_nominal,
                p_nominal=self.p_nominal,
                T_default=self.T_nominal,
            )
        elif self.medium == "AixLib.Media.Antifreeze.PropyleneGlycolWater":
            template_medium = Template(
                filename=os.path.join(
                    dir_templates_network,
                    "medium",
                    "AixLib_Media_Antifreeze_PropyleneGlycolWater.mako",
                )
            )
            mo_medium = template_medium.render_unicode(
                T_nominal=self.T_nominal, fraction_glycol=self.fraction_glycol
            )
        else:
            raise ValueError("No template for chosen medium {}".format(self.medium))

        has_substation_heat_pump = False
        for node in self.nodelist_building:
            if "comp_model" in self.nodes[node]:
                if "HeatPump" in self.nodes[node]["comp_model"]:
                    has_substation_heat_pump = True

        if has_substation_heat_pump:
            template_medium = Template(
                filename=os.path.join(
                    dir_templates_network, "medium", "medium_building.mako"
                )
            )
            mo_medium += template_medium.render_unicode(
                T_nominal=30 + 273.15, p_nominal=3e5, T_default=30 + 273.15
            )

        return mo_medium

    def write_supply_definitions(self):
        """Write the rendered Modelica code for the supply model definitions

        Returns
        -------
        mo_supplies : str
            Rendered Modelica code for the supply definitions
        """
        mo_supplies = ""

        supplies = []
        for node in self.nodelist_building:
            if self.nodes[node]["is_supply_{}".format(self.network_type)]:
                supplies.append(node)

        for i, node in enumerate(supplies):

            # new template path implementation
            if "template_path" in self.nodes[node].keys():
                template_path = self.nodes[node]["template_path"]
            else:
                template_path = None

            model = self.nodes[node]["comp_model"]

            # See https://softwareengineering.stackexchange.com/questions/182093
            # mo_supply = self.templates[model]['render'](node, i, len(supplies))
            # Use new template class
            supply_template = UESTemplates(
                model_name=model,
                model_type="Supply",
                template_path=template_path)
            mo_supply = supply_template.render(
                node_data=self.nodes[node], i=i, number_of_instances=len(supplies)
            )
            mo_supplies += mo_supply

            if node != supplies[-1]:
                mo_supplies += "\n"

        return mo_supplies

    def write_t_ground_definitions(self):
        """Write the rendered Modelica code for the ground temperature def

        Returns
        -------
        mo_t_ground : str
            Rendered Modelica code for the ground temperature definition
        """
        dir_templates_network = os.path.join(self.template_directory, "network")

        template_ground = Template(
            filename=os.path.join(
                dir_templates_network, "ground", "PrescribedTemperature.mako"
            )
        )

        mo_t_ground = template_ground.render_unicode()

        return mo_t_ground

    def write_demand_definitions(self):
        """Write the rendered Modelica code for the demand model definitions

        Returns
        -------
        mo_demands : str
            Rendered Modelica code for the demand definitions
        """
        mo_demands = ""

        demands = []
        for node in self.nodelist_building:
            if not self.nodes[node]["is_supply_{}".format(self.network_type)]:
                demands.append(node)

        for i, node in enumerate(demands):
            msg = "No component model specified"
            assert "comp_model" in self.nodes[node], msg

            # new template path implementation
            if "template_path" in self.nodes[node].keys():
                template_path = self.nodes[node]["template_path"]
            else:
                template_path = None

            model = self.nodes[node]["comp_model"]

            # New Template
            demand_template = UESTemplates(
                model_name=model,
                model_type="Demand",
                template_path=template_path)
            mo_demand = demand_template.render(
                node_data=self.nodes[node],
                i=i,
                number_of_instances=len(demands),
                package_name=self.model_name
            )

            mo_demands += mo_demand

            if node != demands[-1]:
                mo_demands += "\n"

        return mo_demands

    def _write_mo_t_ground_kusuda(self):
        """Write Modelica code for ground temperature Kusuda model

        Returns
        -------
        mo : str
            Rendered Modelica code
        """
        dir_templates_ground = os.path.join(self.template_directory, "system", "ground")

        assert "T_mean" in self.params_kusuda, "T_mean missing from self.params_kusuda"
        assert "T_amp" in self.params_kusuda, "T_amp missing from self.params_kusuda"
        assert "alpha" in self.params_kusuda, "alpha missing from self.params_kusuda"
        assert (
            "t_shift" in self.params_kusuda
        ), "t_shift missing from self.params_kusuda"
        assert "D" in self.params_kusuda, "D missing from self.params_kusuda"

        model_template = os.path.join(dir_templates_ground, "t_ground_kusuda.mako")
        curr_model_template = Template(filename=model_template)
        mo = curr_model_template.render_unicode(
            name_model=self.model_name,
            T_mean=self.params_kusuda["T_mean"],
            T_amp=self.params_kusuda["T_amp"],
            alpha=self.params_kusuda["alpha"],
            t_shift=self.params_kusuda["t_shift"],
            D=self.params_kusuda["D"],
        )

        return mo

    def _write_mo_t_ground_table(self):
        """Write Modelica code for ground temperature table model

        Returns
        -------
        mo : str
            Rendered Modelica code
        """
        dir_templates_ground = os.path.join(self.template_directory, "system", "ground")

        model_template = os.path.join(dir_templates_ground, "t_ground_table.mako")
        curr_model_template = Template(filename=model_template)
        mo = curr_model_template.render_unicode(name_model=self.model_name)

        return mo

    def write_pipe_definitions(self):
        """Write the rendered Modelica code for the pipe model definitions

        Returns
        -------
        mo_pipes : str
            Rendered Modelica code for the pipe definitions
        """
        mo_pipes = ""

        for node in self.nodelist_pipe:
            assert "comp_model" in self.nodes[node], "No component model specified"

            # new template path implementation
            if "template_path" in self.nodes[node].keys():
                template_path = self.nodes[node]["template_path"]
            else:
                template_path = None

            model = self.nodes[node]["comp_model"]

            # New Template
            pipe_template = UESTemplates(
                model_name=model,
                model_type="Pipe",
                template_path=template_path)
            mo_pipe = pipe_template.render(node_data=self.nodes[node])
            mo_pipes += mo_pipe

            if self.add_return_network:
                return_node_data = self.nodes[node]
                return_node_data["name"] = return_node_data["name"] + "R"
                return_node_data["position"] = sg.Point(
                    return_node_data["position"].x - 5,
                    return_node_data["position"].y - 5)
                mo_pipe_return = pipe_template.render(node_data=return_node_data)
                mo_pipes += mo_pipe_return
                # TODO find better workaround
                return_node_data["name"] = return_node_data["name"][:-1]

            # TODO add ground around pipe function
            # if self.add_ground_around_pipe:
            #     mo_ground = self._write_ground_around_pipe(node)
            #     mo_pipes += mo_ground

            if node != self.nodelist_pipe[-1]:
                mo_pipes += "\n"

        return mo_pipes

    def write_annotations(self):
        """Write the rendered Modelica code for annotations

        Returns
        -------
        mo_ann : str
            Rendered Modelica code for the annotations
        """
        dir_templates_network = os.path.join(self.template_directory, "network")

        mo_ann = "  annotation (\n"

        template_diagram = Template(
            filename=os.path.join(dir_templates_network, "annotations", "diagram.mako")
        )
        diagram = template_diagram.render_unicode(
            min_x=self.min_position.x,
            min_y=self.min_position.y,
            max_x=self.max_position.x,
            max_y=self.max_position.y,
        )
        mo_ann += diagram

        uses = "    uses("
        for library in self.uses:
            if library != self.uses[-1]:
                uses += "{},".format(library)
            else:
                uses += "{}),\n".format(library)
        mo_ann += uses

        template_documentation = Template(
            filename=os.path.join(
                dir_templates_network, "annotations", "documentation.mako"
            )
        )
        documentation = template_documentation.render_unicode(
            documentation=self.documentation,
            now=datetime.datetime.now(),
            version=__version__,
        )
        mo_ann += documentation

        template_experiment = Template(
            filename=os.path.join(
                dir_templates_network, "annotations", "experiment.mako"
            )
        )
        experiment = template_experiment.render_unicode(
            stop_time=self.stop_time,
            interval=self.timestep,
            solver=self.solver,
            tolerance=self.tolerance,
        )
        mo_ann += experiment
        mo_ann += "  );\n"

        return mo_ann

    def write_input_connections(self):
        """Write the rendered Modelica code for the input connections

        Returns
        -------
        mo_con : str
            Rendered Modelica code for the input connections
        """
        demands = []
        supplies = []
        for node in self.nodelist_building:
            if self.nodes[node]["is_supply_{}".format(self.network_type)]:
                supplies.append(node)
            else:
                demands.append(node)

        mo_con = ""

        for node in demands:
            name = self.nodes[node]["name"]

            # new template path implementation
            if "template_path" in self.nodes[node].keys():
                template_path = self.nodes[node]["template_path"]
            else:
                template_path = None

            demand_template = UESTemplates(
                model_name=self.nodes[node]["comp_model"],
                model_type="Demand",
                template_path=template_path
            )
            list_of_connectors = demand_template.call_function("get_connector_names")
            if len(list_of_connectors) != 0:
                connector_name = list_of_connectors[0]
                # TODO assert len()>1
                connection = "  connect({}{}, demand{}.{});\n".format(
                    name, connector_name, name, connector_name
                )
                mo_con += connection
        mo_con += "\n"

        for node in supplies:
            model = self.nodes[node]["comp_model"]

            # new template path implementation
            if "template_path" in self.nodes[node].keys():
                template_path = self.nodes[node]["template_path"]
            else:
                template_path = None

            name = self.nodes[node]["name"]
            supply_template = UESTemplates(
                model_name=model,
                model_type="Supply",
                template_path=template_path)
            connector_list = supply_template.call_function("get_connector_names")
            if len(connector_list) != 0:
                for connector in connector_list:
                    connection = "  connect({}{}, supply{}.{});\n".format(
                        name, connector, name, connector
                    )
                    mo_con += connection

        mo_con += "\n"
        mo_con += "  connect(TGroundIn, TGround.T);\n"
        mo_con += "\n"

        for node in self.nodelist_pipe:
            name = self.nodes[node]["name"]
            if self.add_ground_around_pipe:
                mo_con += "  connect(TGround.port, ground{}.port_b);\n".format(name)
                mo_con += "  connect(ground{}.port_a, pipe{}.heatPort);\n".format(
                    name, name
                )
                if self.add_return_network:
                    mo_con += "  connect(TGround.port, ground{}R.port_b);\n".format(
                        name
                    )
                    mo_con += "  connect(ground{}R.port_a, pipe{}R.heatPort);\n".format(
                        name, name
                    )

            else:
                mo_con += "  connect(TGround.port, pipe{}.heatPort);\n".format(name)
                if self.add_return_network:
                    mo_con += "  connect(TGround.port, pipe{}R.heatPort);\n".format(
                        name
                    )

        return mo_con

    def write_network_connections(self):
        """Write the rendered Modelica code for the network connections

        Returns
        -------
        mo_con : str
            Rendered Modelica code for the network connections
        """
        dir_templates_network = os.path.join(self.template_directory, "network")

        mo_con = ""

        template_connections = Template(
            filename=os.path.join(
                dir_templates_network, "connections", "supply_network.mako"
            )
        )
        for edge in self.edges():
            mo_con += template_connections.render_unicode(
                con1=self.edges[edge[0], edge[1]]["con1"],
                con2=self.edges[edge[0], edge[1]]["con2"],
                x1=self.nodes[edge[0]]["position"].x,
                y1=self.nodes[edge[0]]["position"].y,
                x2=self.nodes[edge[1]]["position"].x,
                y2=self.nodes[edge[1]]["position"].y,
            )
            if self.add_return_network:
                if self.nodes[edge[0]]["node_type"] == "building":
                    mo_con += template_connections.render_unicode(
                        con1=self.edges[edge[0], edge[1]]["con1R"],
                        con2=self.edges[edge[0], edge[1]]["con2R"],
                        x1=self.nodes[edge[0]]["position"].x - 5,
                        y1=self.nodes[edge[0]]["position"].y - 5,
                        x2=self.nodes[edge[1]]["position"].x - 5,
                        y2=self.nodes[edge[1]]["position"].y - 5
                    )
                elif self.nodes[edge[1]]["node_type"] == "building":
                    mo_con += template_connections.render_unicode(
                        con1=self.edges[edge[0], edge[1]]["con1R"],
                        con2=self.edges[edge[0], edge[1]]["con2R"],
                        x1=self.nodes[edge[0]]["position"].x - 5,
                        y1=self.nodes[edge[0]]["position"].y - 5,
                        x2=self.nodes[edge[1]]["position"].x - 5,
                        y2=self.nodes[edge[1]]["position"].y - 5
                    )
                else:
                    mo_con += template_connections.render_unicode(
                        con1=self.edges[edge[0], edge[1]]["con1R"],
                        con2=self.edges[edge[0], edge[1]]["con2R"],
                        x1=self.nodes[edge[0]]["position"].x,
                        y1=self.nodes[edge[0]]["position"].y,
                        x2=self.nodes[edge[1]]["position"].x,
                        y2=self.nodes[edge[1]]["position"].y
                    )





                # mo_con += template_connections.render_unicode(
                #     con1=self.edges[edge[0], edge[1]]["con1R"],
                #     con2=self.edges[edge[0], edge[1]]["con2R"],
                #     x1=self.nodes[edge[0]]["position"].x - 5,
                #     y1=self.nodes[edge[0]]["position"].y - 5,
                #     x2=self.nodes[edge[1]]["position"].x - 5,
                #     y2=self.nodes[edge[1]]["position"].y - 5
                # )

                # mo_con += "  connect({}, {});\n".format(
                #     self.edges[edge[0], edge[1]]["con1R"],
                #     self.edges[edge[0], edge[1]]["con2R"],
                # )

        return mo_con

    def write_network_model(self, save_at):
        """Writes a network model to Modelica code file

        Parameters
        ----------
        save_at : str
            Path where to create the subfolders, in which the Modelica
            files are saved
        """
        # The following distinction is from
        # https://stackoverflow.com/questions/29840849
        # in order to write pretty files without empty lines in both Python
        # 2 and 3 on Windows
        if sys.version_info[0] == 2:  # For Python 2
            access = "wb"
            kwargs = {}
        else:
            access = "wt"
            kwargs = {"newline": ""}

        name_file = os.path.join(save_at, self.model_name + ".mo")
        with open(name_file, access, **kwargs) as out_file:
            out_file.write("""model {}\n""".format(self.model_name))
            out_file.write("""  "{}"\n""".format(self.doc_string))
            out_file.write("\n")
            out_file.write(self.write_medium_definition())
            out_file.write(self.write_supply_definitions())
            out_file.write("\n")
            out_file.write(self.write_demand_definitions())
            out_file.write("\n")
            out_file.write(self.write_pipe_definitions())
            out_file.write("\n")
            out_file.write(self.write_t_ground_definitions())
            out_file.write("\n")

            if self.control_pressure != {}:
                out_file.write(
                    self.write_output_connector(
                        name="dpOut", unit="Pa", annotation=True
                    )
                )
                out_file.write("\n")

            if self.with_heat_flow_output:
                out_file.write(
                    self.write_output_connector(
                        name="Q_flow_out", unit="W", annotation=False
                    )
                )
                out_file.write("\n")

            if self.with_heat_loss_output:
                model_template = os.path.join(
                    self.template_directory,
                    "network",
                    "pipe_heat_loss.mako",
                )
                curr_model_template = Template(filename=model_template)
                mo = curr_model_template.render_unicode()
                out_file.write(mo)

                out_file.write(
                    self.write_output_connector(
                        name="Pipes_Heat_Loss", unit="W", annotation=False
                    )
                )
                out_file.write("\n")

            out_file.write("\n")
            out_file.write("""equation\n""")
            out_file.write(self.write_network_connections())
            out_file.write("\n")
            out_file.write(self.write_input_connections())
            out_file.write("\n")

            if self.control_pressure != {}:
                node = self.control_pressure["building"]
                name_building = self.nodes[node]["name"]
                print("Using {} for control".format(name_building))
                con_dp = "  connect(demand{}.dpOut, dpOut);\n".format(name_building)
                out_file.write(con_dp)
                out_file.write("\n")

            if self.with_heat_flow_output:
                for node in self.nodelist_building:
                    if self.nodes[node]["is_supply_{}".format(self.network_type)]:
                        name_bldg = self.nodes[node]["name"]
                        con_power = "  connect(supply{}.Q_flow, Q_flow_out);\n".format(
                            name_bldg
                        )
                        out_file.write(con_power)
                        out_file.write("\n")

            if self.with_heat_loss_output:
                con = "  connect(heat_loss_pipes.y, Pipes_Heat_Loss);\n"
                out_file.write(con)
                out_file.write("\n")

            out_file.write(self.write_annotations())
            out_file.write("""end {};\n""".format(self.model_name))

    def write_modelica_package(self, save_at):
        """Writes a system model and inputs to Modelica package

        Parameters
        ----------
        save_at : str
            Path where to create the subfolders, in which the Modelica
            files are saved
        """
        # Create new package directory
        dir_dest = os.path.join(save_at, self.model_name)
        print("dir_dest", dir_dest)
        if not os.path.exists(dir_dest):
            os.mkdir(dir_dest)

        # Write meta data
        if self.meta_data:
            with open(
                os.path.join(dir_dest, 'meta_data.txt'), 'w') as outfile:
                json.dump(self.meta_data, outfile, indent=2)

        # Write package.mo file
        with open(os.path.join(dir_dest, "package.mo"), "w") as package_mo:
            package_mo.write("within ;\n")
            package_mo.write(
                """package {} "Package created with uesmodels"\n""".format(
                    self.model_name
                )
            )
            package_mo.write("end {};\n".format(self.model_name))

        # Write inputs to Resources directory
        dir_resources = os.path.join(dir_dest, "Resources")
        if not os.path.exists(dir_resources):
            os.mkdir(dir_resources)
        dir_inputs = os.path.join(dir_resources, "Inputs")
        if not os.path.exists(dir_inputs):
            os.mkdir(dir_inputs)

        for node in self.nodelist_building:
            if self.nodes[node]["is_supply_{}".format(self.network_type)]:
                name_bldg = self.nodes[node]["name"]

                # read input connectors from supply templates
                if "template_path" in self.nodes[node].keys():
                    template_path = self.nodes[node]["template_path"]
                else:
                    template_path = None
                supply_template = UESTemplates(
                    model_name=self.nodes[node]["comp_model"],
                    model_type="Supply",
                    template_path=template_path
                )
                input_names = supply_template.call_function("get_connector_names")
                for name in input_names:
                    # Write supply temperature input file
                    name_file = "supply_{}_{}.txt".format(name_bldg, name)
                    save_as = os.path.join(dir_inputs, name_file)
                    description = "Supply {} for {}".format(name, name_bldg)

                    self.write_input_txt(
                        save_as=save_as,
                        name_variable=name,
                        time=self.time,
                        values=self.nodes[node][name],
                        description=description,
                        digits=2,
                    )

                # # Write supply pressure input file
                # name_file = 'supply_{}_p_s.txt'.format(name_bldg)
                # save_as = os.path.join(dir_inputs, name_file)
                # description = 'Supply pressure for {} in Pa'.format(name_bldg)
                #
                # self.write_input_txt(
                #     save_as=save_as,
                #     name_variable='p_supply',
                #     time=self.time,
                #     values=self.nodes[node]['p_supply'],
                #     description=description,
                #     digits=1,
                # )

                # if 'feed-in' in self.nodes[node]:
                #     name_file = 'supply_{}_Q_in.txt'.format(name_bldg)
                #     save_as = os.path.join(dir_inputs, name_file)
                #     description = 'Prescribed feed-in for {} in W'.format(name_bldg)
                #
                #     self.write_input_txt(
                #         save_as=save_as,
                #         name_variable='Q_flow',
                #         time=self.time,
                #         values=self.nodes[node]['feed-in'],
                #         description=description,
                #         digits=0,
                #     )

        # Write ground temperature input file
        if self.ground_model == "t_ground_table":
            save_as = os.path.join(dir_inputs, "T_ground.txt")
            description = "Ground temperature in K"

            self.write_input_txt(
                save_as=save_as,
                name_variable="T_ground",
                time=self.time,
                values=self.graph["T_ground"],
                digits=2,
                description=description,
            )

        # Write heat demand input files / old version
        # for node in self.nodelist_building:
        #     if not self.nodes[node]["is_supply_{}".format(self.network_type)]:
        #         name_bldg = self.nodes[node]["name"]
        #         msg = "No data for {}".format(name_bldg)
        #         assert "input_heat" in self.nodes[node], msg

        #         dhw_written = False

        #         if "dhw" in name_bldg:
        #             if not dhw_written:
        #                 name_file = "demand_dhw.txt".format(name_bldg)
        #                 save_as = os.path.join(dir_inputs, name_file)
        #                 description = "Heat demand for dhw in W"

        #                 dhw = []
        #                 for val in self.nodes[node]["input_heat"]:
        #                     dhw.append(val / max(self.nodes[node]["input_heat"]))

        #                 self.write_input_txt(
        #                     save_as=save_as,
        #                     name_variable="demand",
        #                     time=self.time,
        #                     values=dhw,
        #                     digits=4,
        #                     description=description,
        #                 )
        #                 dhw_written = True
        #         else:
        #             name_file = "demand_{}_heat.txt".format(name_bldg)
        #             save_as = os.path.join(dir_inputs, name_file)
        #             description = "Heat demand for {} in W".format(name_bldg)

        #             self.write_input_txt(
        #                 save_as=save_as,
        #                 name_variable="demand",
        #                 time=self.time,
        #                 values=self.nodes[node]["input_heat"],
        #                 digits=0,
        #                 description=description,
        #             )

        # Write heat demand input files
        for node in self.nodelist_building:
            if not self.nodes[node]["is_supply_{}".format(self.network_type)]:
                name_bldg = self.nodes[node]["name"]
                msg = "No data for {}".format(name_bldg)
                assert "input_heat" in self.nodes[node], msg

                dhw_written = False

                if "input_dhw" in self.nodes[node].keys():
                    name_file = "demand_{}_dhw.txt".format(name_bldg)
                    save_as = os.path.join(dir_inputs, name_file)
                    description = "Dhw demand for {} in W".format(name_bldg)

                    self.write_input_txt(
                        save_as=save_as,
                        name_variable="demand",
                        time=self.time,
                        values=self.nodes[node]["input_dhw"],
                        digits=0,
                        description=description,
                    )
                if "input_cool" in self.nodes[node].keys():
                    name_file = "demand_{}_cool.txt".format(name_bldg)
                    save_as = os.path.join(dir_inputs, name_file)
                    description = "Cool demand for {} in W".format(name_bldg)

                    self.write_input_txt(
                        save_as=save_as,
                        name_variable="demand",
                        time=self.time,
                        values=self.nodes[node]["input_cool"],
                        digits=0,
                        description=description,
                    )
                if "input_heat" in self.nodes[node].keys():
                    name_file = "demand_{}_heat.txt".format(name_bldg)
                    save_as = os.path.join(dir_inputs, name_file)
                    description = "Heat demand for {} in W".format(name_bldg)

                    self.write_input_txt(
                        save_as=save_as,
                        name_variable="demand",
                        time=self.time,
                        values=self.nodes[node]["input_heat"],
                        digits=0,
                        description=description,
                    )

        # Write package.order file
        with open(os.path.join(dir_dest, "package.order"), "w") as package_ord:
            package_ord.write("{}\n".format(self.model_name))
            package_ord.write("{}\n".format(self.model_name + "_inputs"))

        # Write the network model
        self.write_network_model(save_at=dir_dest)

        # Write the network model into a system model with inputs
        self.write_modelica_system(save_at=dir_dest)

    def write_modelica_system(self, save_at):
        """Writes a system model with inputs

        Parameters
        ----------
        save_at : str
            Path where to store the generated model
        """

        dir_templates_system = os.path.join(self.template_directory, "system")
        path_file = os.path.join(save_at, "{}.mo".format(self.model_name + "_inputs"))

        demands = []
        supplies = []
        for node in self.nodelist_building:
            if self.nodes[node]["is_supply_{}".format(self.network_type)]:
                supplies.append(node)
            else:
                demands.append(node)

        # https://stackoverflow.com/questions/29840849
        if sys.version_info[0] == 2:  # For Python 2
            access = "wb"
            kwargs = {}
        else:
            access = "wt"
            kwargs = {"newline": ""}

        with open(path_file, access, **kwargs) as out_file:
            out_file.write("""model {}\n""".format(self.model_name + "_inputs"))
            out_file.write("""  "System model with inputs for network"\n""")
            out_file.write("""  extends Modelica.Icons.Example;\n""")
            out_file.write("\n")

            model_template = os.path.join(dir_templates_system, "network_model.mako")
            curr_model_template = Template(filename=model_template)
            mo = curr_model_template.render_unicode(name=self.model_name)
            out_file.write(mo)
            out_file.write("\n")

            dhw_written = False
            for i, node in enumerate(demands):
                name = self.nodes[node]["name"]
                # new template path implementation
                if "template_path" in self.nodes[node].keys():
                    template_path = self.nodes[node]["template_path"]
                else:
                    template_path = None

                demand_template_def = UESTemplates(
                    model_name=self.nodes[node]["comp_model"],
                    model_type="Demand",
                    template_path=template_path
                )
                list_of_real_inputs = demand_template_def.call_function(
                    "get_connector_names"
                )
                if len(list_of_real_inputs) != 0:
                    if "dhw" not in name:
                        model_template = os.path.join(
                            dir_templates_system, "demand_inputs.mako"
                        )
                        curr_model_template = Template(filename=model_template)
                        mo = curr_model_template.render_unicode(
                            name_demand=self.nodes[node]["name"],
                            name_model=self.model_name,
                            i=i,
                            number_of_demands=len(demands),
                        )
                        out_file.write(mo)
                    else:
                        if not dhw_written:
                            model_template = os.path.join(
                                dir_templates_system, "demand_input_dhw.mako"
                            )
                            curr_model_template = Template(filename=model_template)
                            mo = curr_model_template.render_unicode(
                                name_model=self.model_name,
                                i=i,
                                number_of_demands=len(demands),
                            )
                            out_file.write(mo)
                            dhw_written = True

            for i, node in enumerate(supplies):
                if "template_path" in self.nodes[node].keys():
                    template_path = self.nodes[node]["template_path"]
                else:
                    template_path = None
                supply_template_def = UESTemplates(
                    model_name=self.nodes[node]["comp_model"],
                    model_type="Supply",
                    template_path=template_path
                )
                list_of_real_inputs = supply_template_def.call_function(
                    "get_connector_names"
                )
                curr_model_template = Template(
                    filename=os.path.join(
                        self.template_directory, "system", "supply_source.mako"
                    )
                )

                # whole section needs to be revised
                # see https://git.rwth-aachen.de/EBC/Team_UES/dhc-networks/uesgraphs_adv/merge_requests/16#note_862663

                if self.control_pressure == {} or not node == self.control_pressure['supply']:
                    for i_in, real_input in enumerate(list_of_real_inputs):
                        mo = curr_model_template.render_unicode(
                            name_supply=self.nodes[node]["name"],
                            name_connector=real_input,
                            name_model=self.model_name,
                            i=i,
                            number_of_supplies=len(supplies),
                            number_of_input=i_in,
                        )
                        out_file.write(mo)
                        out_file.write("\n")
                else:
                    # hardcode needs to be changed
                    list_of_real_inputs.remove("dpIn")
                    for i_in, real_input in enumerate(list_of_real_inputs):
                        mo = curr_model_template.render_unicode(
                            name_supply=self.nodes[node]["name"],
                            name_connector=real_input,
                            name_model=self.model_name,
                            i=i,
                            number_of_supplies=len(supplies),
                            number_of_input=i_in,
                        )
                        out_file.write(mo)
                        out_file.write("\n")

            mo_t_ground = self.templates[self.ground_model]["render"]()
            out_file.write(mo_t_ground)

            if self.control_pressure != {}:
                model_template = os.path.join(dir_templates_system, "control.mako")
                curr_model_template = Template(filename=model_template)
                mo = curr_model_template.render_unicode(
                    dp_set=self.control_pressure["dp"],
                    p_max=self.control_pressure["p_max"],
                    k=self.control_pressure["k"],
                    Ti=self.control_pressure["Ti"]
                )
                out_file.write(mo)

            if self.with_heat_flow_output:
                out_file.write(
                    self.write_output_connector(
                        name="Q_flow_out", unit="W", annotation=False
                    )
                )
                out_file.write("\n")

            if self.with_heat_loss_output:
                out_file.write(
                    self.write_output_connector(
                        name="Pipes_Heat_Loss", unit="W", annotation=False
                    )
                )
                out_file.write("\n")

            out_file.write("""equation\n""")

            for i, node in enumerate(demands):
                name = self.nodes[node]["name"]
                # new template path implementation
                if "template_path" in self.nodes[node].keys():
                    template_path = self.nodes[node]["template_path"]
                else:
                    template_path = None

                demand_template_def = UESTemplates(
                    model_name=self.nodes[node]["comp_model"],
                    model_type="Demand",
                    template_path=template_path
                )
                list_of_real_inputs = demand_template_def.call_function(
                    "get_connector_names"
                )
                if len(list_of_real_inputs) != 0:
                    if "dhw" not in name:
                        demand_template = UESTemplates(
                            model_name=self.nodes[node]["comp_model"], model_type="Demand"
                        )
                        names_input = demand_template.call_function("get_connector_names")
                        # TODO assert if len >0
                        model_template = os.path.join(
                            dir_templates_system, "connections_demands.mako"
                        )
                        curr_model_template = Template(filename=model_template)
                        mo = curr_model_template.render_unicode(
                            name_demand=self.nodes[node]["name"],
                            name_connector=names_input[0],
                            i=i,
                            number_of_demands=len(demands),
                        )
                        out_file.write(mo)
                    else:
                        model_template = os.path.join(
                            dir_templates_system, "connections_demands_dhw.mako"
                        )
                        curr_model_template = Template(filename=model_template)
                        mo = curr_model_template.render_unicode(
                            name_demand=self.nodes[node]["name"],
                            i=i,
                            number_of_demands=len(demands),
                        )
                        out_file.write(mo)

            for i, node in enumerate(supplies):
                if "template_path" in self.nodes[node].keys():
                    template_path = self.nodes[node]["template_path"]
                else:
                    template_path = None
                supply_template_def = UESTemplates(
                    model_name=self.nodes[node]["comp_model"],
                    model_type="Supply",
                    template_path=template_path
                )
                list_of_real_inputs = supply_template_def.call_function(
                    "get_connector_names"
                )
                curr_model_template = Template(
                    filename=os.path.join(
                        self.template_directory, "system", "connections_supply.mako"
                    )
                )

                # whole section needs to be revised
                # see https://git.rwth-aachen.de/EBC/Team_UES/dhc-networks/uesgraphs_adv/merge_requests/16#note_862663

                if self.control_pressure == {} or not node == self.control_pressure['supply']:
                    for i_in, real_input in enumerate(list_of_real_inputs):
                        mo = curr_model_template.render_unicode(
                            name_supply=self.nodes[node]["name"],
                            name_connector=real_input,
                            name_model=self.model_name,
                            i=i,
                            number_of_supplies=len(supplies),
                        )
                        out_file.write(mo)
                        out_file.write("\n")
                else:
                    # hardcode needs to be changed
                    list_of_real_inputs.remove("dpIn")
                    for i_in, real_input in enumerate(list_of_real_inputs):
                        mo = curr_model_template.render_unicode(
                            name_supply=self.nodes[node]["name"],
                            name_connector=real_input,
                            name_model=self.model_name,
                            i=i,
                            number_of_supplies=len(supplies),
                        )
                        out_file.write(mo)
                        out_file.write("\n")

            if self.ground_model == "t_ground_table":
                model_template = os.path.join(
                    dir_templates_system, "connections_t_ground_table.mako"
                )
            elif self.ground_model == "t_ground_kusuda":
                model_template = os.path.join(
                    dir_templates_system, "connections_t_ground_kusuda.mako"
                )
            curr_model_template = Template(filename=model_template)
            mo = curr_model_template.render_unicode()
            out_file.write(mo)

            if self.control_pressure != {}:
                model_template = os.path.join(
                    dir_templates_system, "connections_control.mako"
                )
                curr_model_template = Template(filename=model_template)
                node = self.control_pressure["supply"]
                name_supply = self.nodes[node]["name"]
                mo = curr_model_template.render_unicode(name_supply=name_supply)
                out_file.write(mo)

            if self.with_heat_flow_output:
                for node in self.nodelist_building:
                    if self.nodes[node]["is_supply_{}".format(self.network_type)]:
                        con_power = "  connect(networkModel.Q_flow_out, Q_flow_out);\n"
                        out_file.write(con_power)
                        out_file.write("\n")

            if self.with_heat_loss_output:
                con = "  connect(networkModel.Pipes_Heat_Loss, Pipes_Heat_Loss);\n"
                out_file.write(con)
                out_file.write("\n")

            model_template = os.path.join(dir_templates_system, "annotations.mako")
            curr_model_template = Template(filename=model_template)
            mo = curr_model_template.render_unicode(
                now=datetime.datetime.now(),
                stop_time=self.stop_time,
                interval=self.timestep,
                solver=self.solver,
                tolerance=self.tolerance,
                version=__version__,
            )
            out_file.write(mo)

            out_file.write("""end {};\n""".format(self.model_name + "_inputs"))

    def write_input_txt(
        self, save_as, name_variable, time, values, digits, description=""
    ):
        """Writes a time series to input text file for Resources directory

        Parameters
        ----------

        save_as : str
            File to store input data to
        name_variable : str
            Name of the variable to be referenced in model
        time : list
            Time vector as float in seconds
        values : list
            The input values corresponding to the the time steps
        digits : int
            Number of digits to round to in output table
        description : str
            Optional description to describe the input data
        """
        model_template = os.path.join(
            self.template_directory, "inputs", "template_input.txt"
        )
        input_template = Template(filename=model_template)

        if type(values) is float or type(values) is int:
            values = [values]

        content = input_template.render_unicode(
            name_variable=name_variable,
            rows=len(values),
            time=time,
            values=values,
            digits=digits,
            description=description,
        )

        # The following distinction is from
        # https://stackoverflow.com/questions/29840849
        # in order to write pretty files without empty lines in both Python
        # 2 and 3 on Windows
        if sys.version_info[0] == 2:  # For Python 2
            access = "wb"
            kwargs = {}
        else:
            access = "wt"
            kwargs = {"newline": ""}

        with open(save_as, access, **kwargs) as out_file:
            out_file.write(content)

    def set_control_pressure(
        self,
        name_supply,
        dp,
        name_building="max_distance",
        p_max=10e5,
        k=None,
        ti=None
    ):
        """Set a pressure control to provide a given dp at a building

        Parameters
        ----------
        name_supply : str
            Name of supply to control the pressure in the network
        dp : float
            Pressure difference to be held at reference building
        name_building : str
            Name of the reference building for the network. For default
            `'max_distance'`, the building with the greatest distance from the
            supply unit will be chosen
        p_max : float
            Maximum pressure allowed for the pressure controller
        k : int
            gain of controller
        ti : int
            time constant for integrator block
        """
        assert name_supply in self.nodes_by_name.keys(), "Unknown supply name"
        if name_building != "max_distance":
            assert name_building in self.nodes_by_name.keys(), (
                "Unknown " "building name"
            )

        supply = self.nodes_by_name[name_supply]

        if name_building == "max_distance":
            distances = {}
            for node in self.nodelist_building:
                this_distance = abs(
                    self.nodes[supply]["position"].distance(
                        self.nodes[node]["position"]
                    )
                )
                distances[node] = this_distance

            node_building = max(distances, key=distances.get)
        else:
            node_building = self.nodes_by_name[name_building]

        self.control_pressure = {
            "building": node_building,
            "dp": dp,
            "supply": supply,
            "p_max": p_max,
            "k": k,
            "Ti": ti
        }

    def write_output_connector(self, name, unit, annotation):
        """Write Modelica code for modular output connector

        Parameters
        ----------
        name : str
            Name of of the output connector
        unit : str
            Unit of the output value
        annotation : boolean
            If 'true' annotations will be added to the connector 

        Returns
        -------
        mo : str
            Rendered Modelica code
        """
        model_template = os.path.join(
            self.template_directory, "network", "connections", "output.mako"
        )

        curr_model_template = Template(filename=model_template)
        mo = curr_model_template.render_unicode(
            name=name, unit=unit, annotation=annotation
        )

        return mo
