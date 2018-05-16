"""
This module contains the UESGraph class to describe the urban energy system
"""

import copy
import datetime
from functools import partial
import json
import math
import networkx as nx
import numpy as np
import os
import pandas as pd
import shapely.geometry as sg
import shapely.ops as ops
from shapely import affinity
from shapely.prepared import prep
import uuid
import warnings
import xml.etree.ElementTree

try:
    import pyproj
except:
    msg = 'Could not import pyproj package. Thus, from_osm function ' \
          'is not going to work. If you require it, you have to install ' \
          'from_osm package.'
    warnings.warn(msg)


class UESGraph(nx.Graph):
    """A networkx Graph enhanced for use to describe urban energy systems

    Attributes
    ----------
    name : str
        Name of the graph
    # TODO: delete input ids
    input_ids : dict
        When input is read from json files with ids in their meta data,
        these ids are stored in this dict
    nodelist_street : list
        List of node ids for all street nodes
    nodelist_building : list
        List of node ids for all building nodes
    nodelists_heating : dict
        Dictionary contains nodelists for all heating networks. Keys are names
        of the networks in str format, values are lists of all node ids that
        belong to the network
    nodelists_cooling : dict
        Dictionary contains nodelists for all cooling networks. Keys are names
        of the networks in str format, values are lists of all node ids that
        belong to the network
    nodelists_electricity : dict
        Dictionary contains nodelists for all electricity networks. Keys are
        names of the networks in str format, values are lists of all node
        ids that belong to the network
    nodelists_gas : dict
        Dictionary contains nodelists for all gas networks. Keys are names
        of the networks in str format, values are lists of all node ids that
        belong to the network
    nodelists_others : dict
        Dictionary contains nodelists for all other networks. Keys are names
        of the networks in str format, values are lists of all node ids that
        belong to the network
    network_types : list
        A list of all supported network types with their names in str format
    nodes_by_name : dict
        A dictionary with building names for keys and node numbers for values.
        Used to retrieve node numbers for a given building name.
    positions : dict
        In general, positions in uesgraphs are defined by
        `shapely.geometry.point` objects. This attribute converts the positions
        into a dict of numpy arrays only for use in uesgraphs.visuals, as the
        networkx drawing functions need this format.
    min_position : shapely.geometry.point object
        Position with smallest x and y values in the graph
    max_position : shapely.geometry.point object
        Position with largest x and y values in the graph
    next_node_number : int
        Node number for the next node to be added
    simplification_level : int
        Higher values indicate more simplification of the graph
        0: no simplification
        1: pipes connected in series are simplified to 1 aggregate pipe
    pipeIDs : list
        List of pipeIDs used in the graph
    """

    def __init__(self):
        """Constructor for UESGraph class"""
        super(UESGraph, self).__init__()

        self.name = None
        # TODO: delete
        self.input_ids = {'buildings': None,
                          'nodes': None,
                          'pipes': None,
                          'supplies': None,
                          }
        self.nodelist_street = []
        self.nodelist_building = []
        self.nodelists_heating = {'default': []}
        self.nodelists_cooling = {'default': []}
        self.nodelists_electricity = {'default': []}
        self.nodelists_gas = {'default': []}
        self.nodelists_others = {'default': []}

        self.network_types = ['heating',
                              'cooling',
                              'electricity',
                              'gas',
                              'others']

        self.nodes_by_name = {}
        self.positions = {}
        self.min_position = None
        self.max_position = None

        self.next_node_number= 1001
        self.simplification_level = 0
        self.pipeIDs = []

    @property
    def positions(self):
        for node in self.nodes(data=True):
            if node[0] is not None:
                assert 'position' in node[1], 'No position for:' + str(node[0])
                if node[1]['position'] is not None:
                    self.__positions[node[0]] = np.array([node[1][
                        'position'].x, node[1]['position'].y])
        return self.__positions

    @positions.setter
    def positions(self, value):
        self.__positions = value

    def __str__(self):
        description = '<uesgraphs.UESGraph object>'
        return description

    def __repr__(self):
        description = '<uesgraphs.UESGraph object>'
        return description

    def new_node_number(self):
        """Returns a new 4 digits node number that is not yet used in graph

        Returns
        -------
        new_number : int
            4 digit number not yet used for nodes in graph
        """
        new_number = self.next_node_number
        self.next_node_number += 1

        return new_number

    def add_network(self, network_type, network_id):
        """Adds a new network of specified type

        Parameters
        ----------
        network_type : str
            Specifies the type of the new network as {'heating', 'cooling',
            'electricity', 'gas', 'others'}
        network_id : str
            Name of the new network
        """
        assert network_type in self.network_types, 'Network type not known'
        assert type(network_id) == type(str()), 'Network name must be a string'

        if network_type == 'heating':
            self.nodelists_heating[network_id] = []
        elif network_type == 'cooling':
            self.nodelists_cooling[network_id] = []
        elif network_type == 'electricity':
            self.nodelists_electricity[network_id] = []
        elif network_type == 'gas':
            self.nodelists_gas[network_id] = []
        elif network_type == 'others':
            self.nodelists_others[network_id] = []

    def _update_min_max_positions(self, position):
        """Updates values for min_positions and max_positions

        Parameters
        ----------
        position : shapely.geometry.Point
            Definition of the node position with a Point object
        """
        if type(position) == type(sg.Point(0, 0)):
            if self.min_position is None:
                self.min_position = position
            else:
                if position.x < self.min_position.x:
                    self.min_position = sg.Point(position.x,
                                                 self.min_position.y)
                if position.x > self.max_position.x:
                    self.max_position = sg.Point(position.x,
                                                 self.max_position.y)
            if self.max_position is None:
                self.max_position = position
            else:
                if position.y < self.min_position.y:
                    self.min_position = sg.Point(self.min_position.x,
                                                 position.y)
                if position.y > self.max_position.y:
                    self.max_position = sg.Point(self.max_position.x,
                                                 position.y)

    def add_building(self, name=None, position=None,
                     is_supply_heating=False,
                     is_supply_cooling=False,
                     is_supply_electricity=False,
                     is_supply_gas=False,
                     is_supply_other=False,
                     attr_dict=None,
                     **attr):
        """Adds a building node to the UESGraph

        Parameters
        ----------
        name : str, int, or float
            A name for the building represented by this node. If None is given,
            the newly assigned node number will also be used as name.
        position : shapely.geometry.Point object
            New node's position
        is_supply_heating : boolean
            True if the building contains a heat supply unit, False if not
        is_supply_cooling : boolean
            True if the building contains a cooling supply unit, False if not
        is_supply_electricity : boolean
            True if the building contains an electricity supply unit, False if
            not
        is_supply_gas : boolean
            True if the building contains a gas supply unit, False if not
        is_supply_other : boolean
            True if the building contains a supply unit for a network of
            network type other, False if not
        attr_dict : dictionary, optional (default= no attributes)
            Dictionary of building attributes. Key/value pairs set data
            associated with the building
        attr : keyword arguments, optional
            Set attributes of building using key=value

        Returns
        -------

        node_number : int
            Number of the added node in the graph
        """
        node_number = self.new_node_number()
        if name is None:
            name = node_number

        attr_dict_ues = {
            'name': name,
            'node_type': 'building',
            'position': position,
            'is_supply_heating': is_supply_heating,
            'is_supply_cooling': is_supply_cooling,
            'is_supply_electricity': is_supply_electricity,
            'is_supply_gas': is_supply_gas,
            'is_supply_other': is_supply_other}

        if attr_dict is not None:
            attr_dict_ues.update(attr_dict)

        attr_dict_ues.update(attr)

        self._update_min_max_positions(position)

        self.add_node(node_for_adding=node_number)
        for key in attr_dict_ues.keys():
            self.nodes[node_number][key] = attr_dict_ues[key]

        self.nodelist_building.append(node_number)

        self.nodes_by_name[name] = node_number

        return node_number

    def remove_building(self, node_number):
        """Removes the specified building node from the graph

        Parameters
        ----------
        node_number : int
            Identifier of the node in the graph
        """
        if node_number in self.nodelist_building:
            self.nodelist_building.remove(node_number)
            self.remove_node(node_number)
        else:
            warnings.warn('Node number has not been found in building' +
                          'nodelist. Therefore, node has not been removed.')

    def add_street_node(self,
                        position,
                        resolution=1e-4,
                        check_overlap=True,
                        attr_dict=None,
                        **attr):
        """Adds a street node to the UESGraph

        Parameters
        ----------
        position : shapely.geometry.Point
            Definition of the node position with a shapely Point object
        resolution : float
            Minimum distance between two points in m. If new position is closer
            than resolution to another existing node, the existing node will be
            returned, no new node will be created.
        check_overlap : boolean
            By default, the method checks whether the new position overlaps
            an existing network node. This can be skipped for performance
            reasons by setting check_overlap=False
        attr_dict : dictionary, optional (default= no attributes)
            Dictionary of node attributes. Key/value pairs set data
            associated with the node
        attr : keyword arguments, optional
            Set attributes of node using key=value

        Returns
        -------
        node_number : int
            Number of the added node in the graph
        """
        node_number = self.new_node_number()

        attr_dict_ues = {
            'node_type': 'street',
            'position': position}

        if attr_dict is not None:
            attr_dict_ues.update(attr_dict)

        attr_dict_ues.update(attr)

        self._update_min_max_positions(position)

        check_node = None
        if check_overlap is True:
            # Check if there is already a node at the given position
            for node in self.nodelist_street:
                if position.distance(self.nodes[node]['position']) < resolution:
                    check_node = node

        if check_node is not None:
            return check_node
        else:
            self.add_node(node_for_adding=node_number)
            for key in attr_dict_ues.keys():
                self.nodes[node_number][key] = attr_dict_ues[key]
            self.nodelist_street.append(node_number)

            return node_number


    def remove_street_node(self, node_number):
        """Removes the specified street node from the graph

        Parameters
        ----------
        node_number : int
            Identifier of the node in the graph
        """
        if node_number in self.nodelist_street:
            self.nodelist_street.remove(node_number)
            self.remove_node(node_number)
        else:
            warnings.warn('Node number has not been found in street ' +
                          'nodelist. Therefore, node has not been removed.')

    def add_network_node(self,
                         network_type,
                         network_id='default',
                         name=None,
                         position=None,
                         resolution=1e-4,
                         check_overlap=True,
                         attr_dict=None,
                         **attr):
        """Adds a network node to the UESGraph

        A network node should not be placed at positions where there is already
        a node of the same network or a building node.

        Parameters
        ----------
        network_type : str
            Defines the network type into which to add the node. The string
            must be one of the network_types defined in `self.network_types`.
        network_id : str
            Specifies, to which network of the given type the node belongs.
            If no value is given, the network 'default' will be used. Before
            using a `network_id`, it must be added to the UESGraph with
            `self.add_network()`
        name : str, int, or float
            A name for the network junction represented by this node. If
            None is given, the newly assigned node number will also be used
            as name.
        position : shapely.geometry.Point
            Optional definition of the node position with a shapely Point object
        resolution : float
            Minimum distance between two points in m. If new position is closer
            than resolution to another existing node, the existing node will be
            returned, no new node will be created.
        check_overlap : boolean
            By default, the method checks whether the new position overlaps
            an existing network node. This can be skipped for performance
            reasons by setting check_overlap=False
        attr_dict : dictionary, optional (default= no attributes)
            Dictionary of node attributes. Key/value pairs set data
            associated with the node
        attr : keyword arguments, optional
            Set attributes of node using key=value

        Returns
        -------
        node_number : int
            Number of the added node in the graph
        """
        assert network_type in self.network_types, 'Unknown network type'
        node_number = self.new_node_number()
        if name is None:
            name = node_number

        attr_dict_ues = {
            'node_type': 'network_' + network_type,
            'network_id': 'network_id',
            'position': position,
            'name': name,
        }

        if attr_dict is not None:
            attr_dict_ues.update(attr_dict)

        attr_dict_ues.update(attr)

        self._update_min_max_positions(position)

        if network_type == 'heating':
            nodelist = self.nodelists_heating[network_id]
        elif network_type == 'cooling':
            nodelist = self.nodelists_cooling[network_id]
        elif network_type == 'electricity':
            nodelist = self.nodelists_electricity[network_id]
        elif network_type == 'gas':
            nodelist = self.nodelists_gas[network_id]
        elif network_type == 'others':
            nodelist = self.nodelists_others[network_id]

        # Check if there is already a node at the given position
        if check_overlap is True:
            check_node = None

            for node in nodelist:
                if position.distance(self.nodes[node]['position']) < resolution:
                    check_node = node
            if check_node is None:
                for node in self.nodelist_building:
                    if position.distance(self.nodes[node][
                            'position']) < resolution:
                        check_node = node

            if check_node is not None:
                return check_node
            else:
                self.add_node(node_for_adding=node_number)
                for key in attr_dict_ues.keys():
                    self.nodes[node_number][key] = attr_dict_ues[key]
                if network_type == 'heating':
                    nodelist.append(node_number)
                elif network_type == 'cooling':
                    nodelist.append(node_number)
                elif network_type == 'electricity':
                    nodelist.append(node_number)
                elif network_type == 'gas':
                    nodelist.append(node_number)
                elif network_type == 'others':
                    nodelist.append(node_number)
        else:
            self.add_node(node_for_adding=node_number)
            for key in attr_dict_ues.keys():
                self.nodes[node_number][key] = attr_dict_ues[key]
            if network_type == 'heating':
                nodelist.append(node_number)
            elif network_type == 'cooling':
                nodelist.append(node_number)
            elif network_type == 'electricity':
                nodelist.append(node_number)
            elif network_type == 'gas':
                nodelist.append(node_number)
            elif network_type == 'others':
                nodelist.append(node_number)

        self.nodes_by_name[name] = node_number

        return node_number

    def remove_network_node(self, node_number):
        """Removes the specified network node from the graph

        Parameters
        ----------
        node_number : int
            Identifier of the node in the graph
        """
        #  Search for occurrence of node number within different network dicts
        network_list = [self.nodelists_heating, self.nodelists_cooling,
                        self.nodelists_electricity, self.nodelists_gas,
                        self.nodelists_others]

        found_node = False

        for nodelists in network_list:
            for network in nodelists:
                for node_id in nodelists[network]:
                    if node_id == node_number:
                        found_node = True
                        found_nodelists = nodelists
                        found_network = network
                        break

        if found_node:
            found_nodelists[found_network].remove(node_number)
            self.remove_node(node_number)
        else:
            warnings.warn('Chosen node number is not part of any network ' +
                          'dict. Cannot be removed.')

    def get_building_node(self, name):
        """Returns the node number for a given building name

        Parameters
        ----------
        name : str
            Name of the building

        Returns
        -------
        node_number : int
            Number of the corresponding node
        """
        if name in self.nodes_by_name.keys():
            return self.nodes_by_name[name]
        else:
            print(name, 'not known')

    def get_node_by_position(self, position, resolution=1e-4):
        """
        Returns node name and node_nb for node(s) on input position.
        If no node is placed on position, returns empty dictionary.

        Parameters
        ----------
        position : shapely.geometry.Point
            Queried position
        resolution : float
            Minimum distance between two points in m. If  position is closer
            than resolution to another existing node, the existing node will be
            returned.

        Returns
        -------
        result_dict : dict
            Dictionary of nodes on input position (key: node_id, value: name)
        """
        result_dict = {}

        for node in self:
            if 'position' in self.nodes[node]:
                #  If positions are identical, save name and node_id to dict
                if self.nodes[node]['position'].distance(position) < resolution:
                    node_name = self.nodes[node]['name']
                    result_dict[node] = node_name

        return result_dict

    def create_subgraphs(self, network_type, all_buildings=True, streets=False):
        """Returns a list of subgraphs for each network

        Parameters
        ----------
        network_type : str
            One of the network types defined in `self.network_types`. The
            subgraphs for all networks of the chosen network type will be
            returned
        all_buildings : boolean
            Subgraphs will contain all buildings of uesgraph when
            `all_buildings` is True. If False, only those buildings connected
            to a subgraph's network will be part of the corresponding subgraph
        streets : boolean
            Subgraphs will contain streets if `streets` is True.

        Returns
        -------

        subgraphs : list
            List of uesgraph elements for all networks of chosen `network_type`
        """
        assert network_type in self.network_types or network_type is None or\
            network_type == 'proximity', 'Network type not known'

        if network_type == 'heating':
            nodelists = self.nodelists_heating
        elif network_type == 'cooling':
            nodelists = self.nodelists_cooling
        elif network_type == 'electricity':
            nodelists = self.nodelists_electricity
        elif network_type == 'gas':
            nodelists = self.nodelists_gas
        elif network_type == 'others':
            nodelists = self.nodelists_others
        elif network_type is None:
            nodelists = {}

        subgraphs = {}

        if network_type is not None and network_type != 'proximity':
            if nodelists != {'default': []}:
                for network_id in nodelists.keys():
                    # Largely copied from nx.Graph.subgraphs()
                    bunch = nodelists[network_id] + self.nodelist_building
                    # create new graph and copy subgraph into it
                    H = self.__class__()
                    H.max_position = self.max_position
                    H.min_position = self.min_position
                    # copy node and attribute dictionaries
                    for n in bunch:
                        H.add_node(n)
                        for attr in self.nodes[n]:
                            H.nodes[n][attr] = self.nodes[n][attr]
                    # Add edges
                    for n in H.nodes():
                        for nbr in self.neighbors(n):
                            if nbr in H.nodes():
                                H.add_edge(n, nbr)
                                for attr in self.edges[n, nbr]:
                                    H.edges[n, nbr][attr] = self.edges[
                                        n, nbr][attr]


                    H.graph = self.graph
                    for building in self.nodelist_building:
                        H.nodelist_building.append(building)
                    if network_type == 'heating':
                        H.nodelists_heating[
                            network_id] = self.nodelists_heating[network_id]
                    elif network_type == 'cooling':
                        H.nodelists_cooling[
                            network_id] = self.nodelists_cooling[network_id]
                    elif network_type == 'electricity':
                        H.nodelists_electricity[
                            network_id] = self.nodelists_electricity[
                                network_id]
                    elif network_type == 'gas':
                        H.nodelists_gas[
                            network_id] = self.nodelists_gas[network_id]
                    elif network_type == 'others':
                        H.nodelists_others[
                            network_id] = self.nodelists_others[network_id]
                    H.nodes_by_name = self.nodes_by_name
                    subgraphs[network_id] = H

            if all_buildings is False:
                for network_id in subgraphs.keys():
                    to_remove = []
                    for building in subgraphs[network_id].nodelist_building:
                        if nx.degree(subgraphs[network_id], building) == 0:
                            to_remove.append(building)
                    for remove_me in to_remove:
                        subgraphs[network_id].remove_building(remove_me)
        elif network_type is None:
            # create new graph and copy subgraph into it
            H = self.__class__()
            for building in self.nodelist_building:
                if all_buildings is True:
                    H.add_node(building)
                    for attr in self.nodes[building]:
                        H.nodes[building][attr] = self.nodes[
                            building][attr]
                    H.nodelist_building.append(building)
                    H._update_min_max_positions(self.nodes[building][
                        'position'])
                else:
                    if (self.nodes[building]['is_supply_heating'] is False and
                            self.nodes[building][
                                'is_supply_cooling'] is False and
                            self.nodes[building][
                                'is_supply_electricity'] is False and
                            self.nodes[building][
                                'is_supply_gas'] is False and
                            self.nodes[building][
                                'is_supply_other'] is False):
                        # H.node[building] = self.nodes[building]
                        H.add_node(building)
                        for attr in self.nodes[building]:
                            H.nodes[building][attr] = self.nodes[
                                building][attr]
                        H.nodelist_building.append(building)
                        H._update_min_max_positions(self.nodes[building][
                            'position'])

            subgraphs['default'] = H

        if streets is True:
            for network_id in subgraphs.keys():
                # Add edges
                for n in H.nodes():
                    for nbr in self.neighbors(n):
                        if nbr in H.nodes():
                            H.add_edge(n, nbr)
                            for attr in self.edges[n, nbr]:
                                H.edges[n, nbr][attr] = self.edges[
                                    n, nbr][attr]

        if network_type == 'proximity' and 'proximity' in self.graph:
            H = copy.deepcopy(self)
            H.min_position = None
            proximity = self.graph['proximity']
            for node in self.nodes():
                position = self.nodes[node]['position']
                if not proximity.contains(position):
                    node_type = self.nodes[node]['node_type']
                    if 'network' in node_type:
                        H.remove_network_node(node)
                    elif 'building' in node_type:
                        H.remove_building(node)
                    elif 'street' in node_type:
                        H.remove_street_node(node)
            prox_bounds = self.graph['proximity'].bounds
            new_min = sg.Point(prox_bounds[0], prox_bounds[1])
            new_max = sg.Point(prox_bounds[2], prox_bounds[3])
            H.min_position = new_min
            H.max_position = new_max
            return H

        return subgraphs

    def from_json(self, path, network_type, check_overlap=False):
        """Imports network from json input

        Parameters
        ----------
        path : str
            Path, where input files `substations.json`, `nodes.json`,
            `pipes.json` and `supply.json` are located.
        network_type : str
            Specifies the type of the destination network as {'heating',
            'cooling', 'electricity', 'gas', 'others'}
        check_overlap : Boolean
            By default, the method does not check whether network node
            positions overlap existing network nodes. For `True`, this check
            becomes active.

        """
        node_mapping = {}  # input node number => uesgraphs node number

        # Read nodes to dict
        print('    read nodes...')
        input_file = os.path.join(path, 'nodes.json')
        with open(input_file, 'r') as input:
            nodes = json.load(input)
        if 'input_id' in nodes['meta']:
            self.input_ids['nodes'] = nodes['meta']['input_id']

        node_mapping = {}
        print('******')
        for node in nodes['nodes']:
            # Create position object
            if 'longitude' in node and 'latitude' in node:
                this_position = sg.Point(node['longitude'],
                                         node['latitude'])
                node['position'] = this_position
            elif 'x' in node and 'y' in node:
                this_position = sg.Point(node['x'],
                                         node['y'])
                node['position'] = this_position
            else:
                warnings.warn('No spatial data input data for '
                              'node {}'.format(node))

            # Add buildings
            if 'building' in node['node_type']:
                building_id = node['name']
                new_node = self.add_building(name=building_id,
                                             position=this_position)


            # Add supplies
            # TODO: This currently only supports heating and cooling supplies
            if 'supply' in node['node_type']:
                supply_id = node['name']
                if 'heating' in node['node_type']:
                    new_node = self.add_building(name=supply_id,
                                                 position=this_position,
                                                 is_supply_heating=True)
                if 'cooling' in node['node_type']:
                    new_node = self.add_building(name=supply_id,
                                                 position=this_position,
                                                 is_supply_cooling=True)

            # Add network nodes
            if 'network' in node['node_type']:
                new_node = self.add_network_node(
                    network_type=network_type,
                    name=node['name'],
                    position=this_position,
                    resolution=1e-9,
                    check_overlap=check_overlap,
                )

            # Read additional attributes that have not yet been processed
            already_processed = [
                'longitude',
                'latitude',
                'x',
                'y',
                'name',
                'is_supply_heating',
                'is_supply_cooling',
                'node_type',
            ]
            for attrib in node.keys():
                if attrib not in already_processed:
                    self.nodes[new_node][attrib] = node[attrib]

            # Add node to node mapping
            node_mapping[node['name']] = new_node

        # Add edges
        for pipe in nodes['edges']:
            if 'pipeID' in pipe:
                pipe_id = pipe['pipeID']

            has_diameter = False
            if 'diameter_inner' in pipe:
                diameter = pipe['diameter_inner']
                has_diameter = True
            elif 'diameter' in pipe:
                diameter = pipe['diameter']
                has_diameter = True

            node_0 = node_mapping[pipe['node_0']]
            node_1 = node_mapping[pipe['node_1']]

            self.add_edge(node_0,
                          node_1,
                          )
            if has_diameter:
                self.edges[node_0, node_1]['diameter'] = diameter
            if 'length' in pipe:
                self.edges[node_0, node_1]['length'] = pipe[
                    'length']
            if 'G' in pipe:
                self.edges[node_0, node_1]['G'] = pipe['G']
            if 'pipeID' in pipe:
                self.edges[node_0, node_1]['pipeID'] = pipe['pipeID']
                self.pipeIDs.append(int(pipe_id))
            if 'lambda_insulation' in pipe:
                self.edges[node_0, node_1]['G'] = pipe['lambda_insulation']
            if 'thickness_insulation' in pipe:
                self.edges[node_0, node_1]['G'] = pipe['thickness_insulation']

            for attrib in pipe.keys():
                if attrib not in self.edges[node_0, node_1]:
                    self.edges[node_0, node_1][attrib] = pipe[attrib]


        print(' input_ids were', self.input_ids)
        print('...finished')

    def to_json(self, path, name, description='json export from uesgraph',
                all_data=False, prettyprint=False):
        """Saves UESGraph structure to json files

        Parameters
        ----------
        path : str
            Path where a directory with output files will be created. If
            `None` is given, the json data will not be written to file, but
            only returned. This only works for `format_old=False`.
        name : str
            The newly created output directory at `path` will be named
            `<name>HeatingUES`
        description : str
            A description string that will be written to all json output
            files' meta data.
        all_data : boolean
            If False, only the main data (x, y, name, node_type) will be
            written to the json output. If True, all node data is exported.
        prettyprint : boolean
            If `True`, the JSON file will use an indent of 4 spaces to pretty-
            print the file. By default, a more efficient output without
            indents will be generated

        Returns
        -------
        output_data : dict
            Contents of the nodes.json file following the new format. For
            `format_old=True` the method returns `None`.

        """
        if path is not None:
            workspace = os.path.join(path)
            if not os.path.exists(workspace):
                os.mkdir(workspace)

        nodes = []
        edges = []

        meta = {'description': description,
                'source': 'uesgraphs',
                'name': name,
                'created': str(datetime.datetime.now()),
                'simplification_level': self.simplification_level,
                'input_id': str(uuid.uuid4()),
                'units': {'diameter': 'm',
                          'length': 'm',
                          }
                }

        # Write node data from uesgraph to dict for json output
        for node in self.nodes():
            nodes.append({'x': self.nodes[node]['position'].x,
                          'y': self.nodes[node]['position'].y,
                          })
            if 'name' in self.nodes[node]:
                nodes[-1]['name'] = self.nodes[node]['name']
            else:
                nodes[-1]['name'] = str(node)
            if 'node_type' in self.nodes[node]:
                node_type = self.nodes[node]['node_type']
                if 'building' in node_type:
                    if 'is_supply_heating' in self.nodes[node]:
                        if self.nodes[node]['is_supply_heating'] is True:
                            node_type = 'supply_heating'
                    if 'is_supply_cooling' in self.nodes[node]:
                        if self.nodes[node]['is_supply_cooling'] is True:
                            node_type = 'supply_cooling'
                nodes[-1]['node_type'] = node_type
            if all_data is True:
                for key in self.nodes[node]:
                    if key not in nodes[-1] and key != 'position':
                        nodes[-1][key] = self.nodes[node][key]

        # Write pipe data from uesgraph to dict for json output
        for edge in self.edges():
            if 'pipeID' in self.edges[edge[0], edge[1]]:
                try:
                    pipe_id = str(
                        int(self.edges[edge[0], edge[1]]['pipeID']))
                except:
                    pipe_id = self.edges[edge[0], edge[1]]['pipeID']
            else:
                pipe_id = str(edge[0]) + str(edge[1])

            if 'name' in self.nodes[edge[0]]:
                name_0 = self.nodes[edge[0]]['name']
            else:
                name_0 = str(edge[0])
            if 'name' in self.nodes[edge[1]]:
                name_1 = self.nodes[edge[1]]['name']
            else:
                name_1 = str(edge[1])

            edges.append({'node_0': name_0,
                          'node_1': name_1,
                          'pipeID': str(pipe_id),
                          'name': str(pipe_id),
                          })

            if 'length' in self.edges[edge[0], edge[1]]:
                length = self.edges[edge[0], edge[1]]['length']
            else:
                pos_0 = self.nodes[edge[0]]['position']
                pos_1 = self.nodes[edge[1]]['position']
                length = pos_0.distance(pos_1)
            edges[-1]['length'] = length

            if 'diameter' in self.edges[edge[0], edge[1]]:
                diameter = self.edges[edge[0], edge[1]]['diameter']
                edges[-1]['diameter'] = diameter

            if 'lambda_insulation' in self.edges[edge[0], edge[1]]:
                lambda_insulation = self.edges[edge[0], edge[1]]['lambda_insulation']
                edges[-1]['lambda_insulation'] = lambda_insulation

            if all_data is True:
                for key in self.edges[edge[0], edge[1]]:
                    if key not in edges[-1]:
                        edges[-1][key] = self.edges[edge[0], edge[1]][key]

        # Write json files
        output_data = {'meta': meta,
                       'nodes': nodes,
                       'edges': edges,
                       }

        if path is not None:
            with open(os.path.join(workspace, 'nodes.json'),
                      'w') as outfile:
                if prettyprint:
                    json.dump(output_data, outfile,
                              indent=4
                              )
                else:
                    json.dump(output_data, outfile)
        return output_data

    def from_osm(self,
                 osm_file,
                 name=None,
                 check_boundary=False,
                 transform_positions=True):
        """Imports buildings and streets from OpenStreetMap data in `osm_file`

        If available, the following attributes will be written to the imported
        elements:

        For streets:
        - 'street type' (motorway, trunk,primary, secondary, tertiary,
        residential, unclassified, service, living_street, pedestrian)

        For buildings
        - 'position'
        - 'outlines'
        - 'area'
        - 'addr_street'
        - 'addr_housenumber'
        - 'building_levels'
        - 'building_height'
        - 'building_buildyear'
        - 'building_condition'
        - 'building_roof_shape'
        - 'comments'
        - type of usage ('amenity', 'shop', 'leisure')

        Parameters
        ----------
        osm_file : str
            Full path to osm input file
        name : str
            Name of the city for boundary check
        check_boundary : boolean
            If True, the city boundary will be extracted from the osm file and
            only nodes within this boundary will be accepted
        transform_positions : boolean
            By default, positions are transformed to a coordinate system
            that gives distances in Meter setting the origin (0, 0) at the
            minimum position of the graph. If transform_positions is False,
            the positions will remain in longitude and latitude as read from
            the OSM file.

        Returns
        -------
        self : uesgraph object
            UESGraph for the urban energy system read from osm data
        """
        def latlon2abs(geometry, lat1, lat2):
            """Converts a geometry object from lat/lon to absolute coords

            Taken from http://gis.stackexchange.com/questions/127607/

            Parameters
            ----------
            geometry : a shapely geometry object
            lat1 : float
                First reference latitude
            lat 2 : float
                Second reference latitude

            Returns
            -------
            converted : a shapely geometry object
            """

            converted = ops.transform(
                partial(
                    pyproj.transform,
                    pyproj.Proj(init='EPSG:4326'),
                    pyproj.Proj(
                        proj='aea',
                        lat1=lat1,
                        lat2=lat2)),
                geometry)

            return converted

        print('Starting import from OpenStreetMap file')
        root = xml.etree.ElementTree.parse(osm_file).getroot()

        # Write all node positions to dict
        print('Reading node positions to dict...')
        nodes = {}
        for node in root.findall('node'):
            lon = float(node.get('lon'))
            lat = float(node.get('lat'))
            nodes[node.get('id')] = {'lon': lon,
                                     'lat': lat,
                                     }

        # Define street tags to be used in uesgraph
        street_tags = ['motorway',
                       'trunk',
                       'primary',
                       'secondary',
                       'tertiary',
                       'unclassified',
                       'residential',
                       'service',
                       ]

        streets = []
        # Get city boundaries
        print('Creating boundary polygon...')
        if check_boundary is True:
            city_boundaries_ways = []
            way_counter = 0
            for relation in root.findall('relation'):
                for tag in relation.findall('tag'):
                    if tag.get('k') == 'name' and tag.get(
                            'v') == name:
                        for member in relation.findall('member'):
                            if member.get('type') == 'way':
                                curr_ref = member.get('ref')
                                for way in root.findall('way'):
                                    if way.get('id') == curr_ref:
                                        curr_points = []
                                        for nd in way.findall('nd'):
                                            curr_lon = nodes[nd.get('ref')][
                                                'lon']
                                            curr_lat = nodes[nd.get('ref')][
                                                'lat']
                                            curr_points.append(sg.Point(
                                                curr_lon, curr_lat))
                                        curr_way = sg.LineString(curr_points)
                                        city_boundaries_ways.append(curr_way)
                                        way_counter += 1

            # Create one boundary polygon
            end_points = []
            boundary_coords = []
            unused_boundaries = []
            for city_boundaries_way in city_boundaries_ways[1:]:
                unused_boundaries.append(city_boundaries_way)
            for i in range(len(city_boundaries_ways)):
                if i == 0:
                    for coords in city_boundaries_ways[i].coords:
                        boundary_coords.append(coords)
                else:
                    distances = {}
                    curr_end = boundary_coords[-1]
                    curr_end_point = sg.Point(curr_end[0], curr_end[1])
                    end_points.append(curr_end_point)
                    for j in range(len(unused_boundaries)):
                        next_start = unused_boundaries[j].coords[0]
                        next_start_point = sg.Point(next_start[0], next_start[1])
                        distance_0 = curr_end_point.distance(next_start_point)
                        next_end = unused_boundaries[j].coords[-1]
                        next_end_point = sg.Point(next_end[0], next_end[1])
                        distance_1 = curr_end_point.distance(next_end_point)
                        distances[distance_0] = [j, 0]
                        distances[distance_1] = [j, 1]

                    min_distance = min(distances.keys())
                    nearest_boundary = distances[min_distance][0]
                    if distances[min_distance][1] == 0:
                        for coords in unused_boundaries[nearest_boundary].coords:
                                boundary_coords.append(coords)
                    elif distances[min_distance][1] == 1:
                        for coords in unused_boundaries[
                                          nearest_boundary].coords[::-1]:
                                boundary_coords.append(coords)
                    del unused_boundaries[distances[min_distance][0]]
            city_boundary = sg.Polygon(boundary_coords)

        # Read buildings and streets
        print('Read building polygons and street ways...')
        all_building_data = {}
        all_street_ways = []
        for way in root.findall('way'):
            curr_positions = []
            curr_dict = {}
            outlines_building = []
            is_building = False
            for nd in way.findall('nd'):
                curr_lat = float(nodes[nd.get('ref')]['lat'])
                curr_lon = float(nodes[nd.get('ref')]['lon'])
                curr_positions.append((curr_lon, curr_lat))
                outlines_building.append([curr_lat, curr_lon])

            for tag in way.findall('tag'):
                if tag.get('k') == 'building':
                    if len(curr_positions) > 2:
                        curr_way = sg.Polygon(curr_positions)
                        curr_dict['polygon'] = curr_way
                        curr_dict['outlines'] = outlines_building
                        curr_dict['comment'] = tag.get('v')
                        is_building = True
                if tag.get('k') == 'addr:housenumber':
                    curr_dict['addr_housenumber'] = tag.get('v')
                if tag.get('k') == 'addr:street':
                    curr_dict['addr_street'] = tag.get('v')
                if tag.get('k') == 'building:levels':
                    curr_dict['building_levels'] = tag.get('v')
                if tag.get('k') == 'leisure':
                    curr_dict['leisure'] = tag.get('v')
                if tag.get('k') == 'name':
                    curr_dict['name'] = tag.get('v')
                if tag.get('k') == 'shop':
                    curr_dict['shop'] = tag.get('v')
                if tag.get('k') == 'amenity':
                    curr_dict['amenity'] = tag.get('v')
                if tag.get('k') == 'building:roof:shape':
                    curr_dict['building_roof_shape'] = tag.get('v')
                if tag.get('k') == 'building:buildyear':
                    curr_dict['building_buildyear'] = tag.get('v')
                if tag.get('k') == 'building:condition':
                    curr_dict['building_condition'] = tag.get('v')
                if tag.get('k') == 'building:height':
                    curr_dict['building_height'] = tag.get('v')

                if tag.get('k') == 'highway' and tag.get('v') in street_tags:
                    all_street_ways.append([])
                    for i in range(len(curr_positions)):
                        curr_position = sg.Point(curr_positions[i][0],
                                                 curr_positions[i][1])
                        all_street_ways[-1].append(curr_position)
            if is_building is True:
                all_building_data[way.get('id')] = curr_dict

        # Filter buildings and streets for locations within boundary
        street_ways = []
        if check_boundary is True:
            print('Filtering buildings and streets...')
            prepared_boundary = prep(city_boundary)
            building_data = {}
            for id in all_building_data.keys():
                if city_boundary.contains(all_building_data[id]['polygon']):
                    building_data[id] = all_building_data[id]

            for street_way in all_street_ways:
                street_ways.append(filter(prepared_boundary.contains,
                                          street_way))
        else:
            building_data = all_building_data
            street_ways = all_street_ways

        print('Add buildings to graph...')
        counter = 0
        curr_keys = list(building_data.keys())
        ordered_keys = sorted(curr_keys)  # Same node ids for same input
        for id in ordered_keys:
            curr_way = building_data[id]['polygon']
            curr_position = curr_way.centroid
            geom_aea = latlon2abs(curr_way,
                                  curr_way.bounds[1],
                                  curr_way.bounds[3])
            counter += 1
            building = self.add_building(position=curr_position)
            self.nodes[building]['area'] = geom_aea.area
            self.nodes[building]['osm_id'] = id
            self.nodes[building]['polygon'] = building_data[id]['polygon']
            self.nodes[building]['outlines'] = building_data[id]['outlines']
            self.nodes[building]['comment'] = building_data[id]['comment']
            if 'addr_street' in building_data[id]:
                self.nodes[building]['addr_street'] = building_data[id][
                    'addr_street']
            if 'addr_housenumber' in building_data[id]:
                self.nodes[building]['addr_housenumber'] = building_data[id][
                    'addr_housenumber']
            if 'building_levels' in building_data[id]:
                self.nodes[building]['building_levels'] = building_data[id][
                    'building_levels']
            if 'leisure' in building_data[id]:
                self.nodes[building]['leisure'] = building_data[id][
                    'leisure']
            if 'name' in building_data[id]:
                self.nodes[building]['name'] = building_data[id][
                    'name']
            if 'shop' in building_data[id]:
                self.nodes[building]['shop'] = building_data[id][
                    'shop']
            if 'amenity' in building_data[id]:
                self.nodes[building]['amenity'] = building_data[id][
                    'amenity']
            if 'building_roof_shape' in building_data[id]:
                self.nodes[building]['building_roof_shape'] = building_data[id][
                    'building_roof_shape']
            if 'building_buildyear' in building_data[id]:
                self.nodes[building]['building_buildyear'] = building_data[id][
                    'building_buildyear']
            if 'building_condition' in building_data[id]:
                self.nodes[building]['building_condition'] = building_data[id][
                    'building_condition']
            if 'building_height' in building_data[id]:
                    self.nodes[building]['building_height'] = building_data[id][
                        'building_height']

        print('Add streets to graph...')
        for street_way in street_ways:
            street_nodes = []
            to_line_string = []
            for curr_position in street_way:
                street_nodes.append(self.add_street_node(
                                    position=curr_position))
                to_line_string.append(curr_position)
                if len(street_nodes) > 1:
                    if street_nodes[-2] != street_nodes[-1]:
                        self.add_edge(street_nodes[-2], street_nodes[-1],
                                      network_type='street')

            if len(to_line_string) > 1:
                streets.append(sg.LineString(to_line_string))

        # Add boundary to uesgraph
        if check_boundary is True:
            self.graph['boundary'] = city_boundary

        # Transform to new coordinate system
        if transform_positions is True:
            new_min = latlon2abs(self.min_position,
                                 self.min_position.y,
                                 self.max_position.y)
            new_max = latlon2abs(self.max_position,
                                 self.min_position.y,
                                 self.max_position.y)

            for node in self.nodes():
                new_position = latlon2abs(self.nodes[node]['position'],
                                          self.min_position.y,
                                          self.max_position.y)
                new_x = new_position.x - new_min.x
                new_y = new_position.y - new_min.y

                self.nodes[node]['position'] = sg.Point(new_x, new_y)

            self.min_position = sg.Point(0, 0)
            self.max_position = sg.Point(new_max.x-new_min.x,
                                         new_max.y-new_min.y)

            transformed_streets = []
            for street in streets:
                transformed_street = latlon2abs(street,
                                        self.min_position.y,
                                        self.max_position.y)
                to_line_string = []
                for point in transformed_street.coords:
                    to_line_string.append(sg.Point(point[0]-new_min.x,
                                                   point[1]-new_min.y))

                transformed_streets.append(sg.LineString(to_line_string))

            streets = transformed_streets
            self.graph['transformed'] = True

        self.graph['from_osm'] = True

        self.graph['streets'] = streets
        print('Finished import from OpenStreetMap data\n')

        return self

    def number_of_nodes(self, node_type):
        """
        Returns number of nodes for given `node_type`

        Parameters
        ----------
        node_type : str
            {'building', 'street', 'heating', 'cooling', 'electricity',
            'gas', 'other'}

        Returns
        -------
        number_of_nodes : int
            The number of nodes for the given `node_type`
        """
        if node_type == 'building':
            number_of_nodes = len(self.nodelist_building)
        elif node_type == 'street':
            number_of_nodes = len(self.nodelist_street)
        else:
            if node_type == 'heating':
                nodelists = list(self.nodelists_heating.values())
            elif node_type == 'cooling':
                nodelists = list(self.nodelists_cooling.values())
            elif node_type == 'electricity':
                nodelists = list(self.nodelists_electricity.values())
            elif node_type == 'gas':
                nodelists = list(self.nodelists_gas.values())
            elif node_type == 'other':
                nodelists = list(self.nodelists_others.values())
            number_of_nodes = 0
            for nodelist in nodelists:
                number_of_nodes += len(nodelist)

        return number_of_nodes

    def calc_network_length(self, network_type):
        """
        Calculates the length of all edges for given `network_type`

        Parameters
        ----------
        network_type : str
            One of the network types defined in `self.network_types`

        Returns
        -------
        total_length : float
            Total length of all edges for given `network_type` in m
        """
        total_length = 0
        for edge in self.edges():
            if network_type in self.nodes[edge[0]]['node_type'] or \
                            network_type in self.nodes[edge[1]]['node_type']:
                # Taken from http://gis.stackexchange.com/questions/127607/
                curr_way = sg.LineString([self.nodes[edge[0]]['position'],
                                          self.nodes[edge[1]]['position']])
                geom_aea = ops.transform(
                    partial(
                        pyproj.transform,
                        pyproj.Proj(init='EPSG:4326'),
                        pyproj.Proj(
                            proj='aea',
                            lat1=curr_way.bounds[1],
                            lat2=curr_way.bounds[3])),
                    curr_way)
                total_length += geom_aea.length

        return round(total_length, 2)

    def calc_total_building_ground_area(self):
        """
        Returns the sum of all available building ground areas in m**2

        Returns
        -------
        total_ground_area : float
            Sum of all available building ground areas in m**2
        """
        total_ground_area = 0
        counter = 0
        for building in self.nodelist_building:
            if 'area' in self.nodes[building]:
                total_ground_area += self.nodes[building]['area']
            else:
                counter += 1

        if counter > 0:
            warnings.warn('{} of {} buildings have no area '
                          'information'.format(counter,
                                               self.number_of_nodes(
                                                   'building')))

        return total_ground_area

    def rotate(self, degrees):
        """
        Rotates all nodes of the graph by `degrees`

        Parameters
        ----------
        degrees : float
            Value of degrees for rotation
        """

        # Find center point of network to plot
        node_points = []
        for node in self.nodes():
            node_points.append(self.nodes[node]['position'])
        center_point = sg.MultiPoint(node_points).envelope.centroid

        self.min_position = None
        self.max_position = None

        for node in self.nodes():
            self.nodes[node]['position'] = affinity.rotate(
                self.nodes[node]['position'],
                degrees,
                origin=center_point)
            self._update_min_max_positions(self.nodes[node]['position'])

    def network_simplification(self, network_type, network_id='default'):
        """Simplifies a pipe network by replacing serial pipes

        Parameters
        ----------
        network_type : str
            Specifies the type of the network as {'heating', 'cooling',
            'electricity', 'gas', 'others'}
        network_id : str
            Name of the network
        """
        def group_nodes(node, group):
            """Recursive function to find node groups for simplification

            Parameters
            ----------
            node : int
                Node number
            group : dict
                This dict collects a path of pipes to be replaced and the
                end nodes to be kept

            Returns
            -------
            group : list
            """
            if node not in group['path']:
                group['path'].append(node)
            neighbors = nx.neighbors(self, node)
            for neighbor in neighbors:
                if nx.degree(self, neighbor) == 2 and neighbor in nodelist:
                    if neighbor not in group['path']:
                        group['path'].append(neighbor)
                        group = group_nodes(neighbor, group)
                else:
                    if neighbor not in group['ends']:
                        group['ends'].append(neighbor)
            return group

        # Get nodelist for the chosen network
        if network_type == 'heating':
            nodelists = self.nodelists_heating
        elif network_type == 'cooling':
            nodelists = self.nodelists_cooling
        elif network_type == 'electricity':
            nodelists = self.nodelists_electricity
        elif network_type == 'gas':
            nodelists = self.nodelists_gas
        elif network_type == 'other':
            nodelists = self.nodelists_others

        assert network_id in nodelists.keys(), 'Unknown network_id'

        nodelist = nodelists[network_id]

        keep = []
        for node in nodelist:
            if nx.degree(self, node) > 2:
                keep.append(node)

        simplification_finished = False

        while simplification_finished is False:
            group = {'ends': [], 'path': []}
            simplification_finished = True
            for found_node in nodelist:
                if nx.degree(self, found_node) == 2 and found_node not in keep:
                    simplification_finished = False
                    break

            if simplification_finished is False:
                group = group_nodes(found_node, group)

                shortest_path = nx.shortest_path(self,
                                                 group['ends'][0],
                                                 group['ends'][1])

                length_total = 0
                diameter_weights = 0
                dIns_weights = 0
                kIns_weights = 0
                fac_weights = 0
                m_flow_nom_weights = 0
                for i in range(len(shortest_path)-1):
                    length = self.edges[shortest_path[i], shortest_path[
                        i+1]]['length']
                    diameter = self.edges[shortest_path[i], shortest_path[
                        i+1]]['diameter']
                    length_total += length
                    diameter_weights += diameter * length
                    if 'dIns' in self.edges[shortest_path[i],
                                            shortest_path[i+1]]:
                        dIns = self.edges[shortest_path[i], shortest_path[
                            i+1]]['dIns']
                        dIns_weights += dIns * length
                    if 'kIns' in self.edges[shortest_path[i],
                                            shortest_path[i+1]]:
                        kIns = self.edges[shortest_path[i], shortest_path[
                            i+1]]['kIns']
                        kIns_weights += kIns * length
                    if 'fac' in self.edges[shortest_path[i],
                                            shortest_path[i+1]]:
                        fac = self.edges[shortest_path[i], shortest_path[
                            i+1]]['fac']
                        fac_weights += fac * length
                    if 'm_flow_nominal' in self.edges[shortest_path[i],
                                            shortest_path[i+1]]:
                        m_flow_nominal = self.edges[shortest_path[i],
                            shortest_path[i+1]]['m_flow_nominal']
                        m_flow_nom_weights += m_flow_nominal * length

                for node in group['path']:
                    self.remove_network_node(node)

                self.add_edge(group['ends'][0], group['ends'][1],
                              length=length_total,
                              diameter=diameter_weights/length_total,
                              pipeID='{}{}'.format(group['ends'][0],
                                                   group['ends'][1]))

                if dIns_weights != 0:
                    self.edges[group['ends'][0], group['ends'][1]][
                        'dIns'] = dIns_weights / length_total
                if kIns_weights != 0:
                    self.edges[group['ends'][0], group['ends'][1]][
                        'kIns'] = kIns_weights / length_total
                if fac_weights != 0:
                    self.edges[group['ends'][0], group['ends'][1]][
                        'fac'] = fac_weights / length_total
                if m_flow_nom_weights != 0:
                    self.edges[group['ends'][0], group['ends'][1]][
                        'm_flow_nominal'] = m_flow_nom_weights / length_total

        self.simplification_level = 1

    def remove_unconnected_nodes(self, network_type,
                                 network_id='default',
                                 max_iter=10):
        """Removes any edges and network nodes not connected to a supply node

        Parameters
        ----------
        network_type : str
            Specifies the type of the network as {'heating', 'cooling',
            'electricity', 'gas', 'others'}
        network_id : str
            Name of the network
        max_iter : int
            Maximum number of iterations

        Returns
        -------
        removed : list
            Names of removed network nodes
        """
        removed = []
        if network_type == 'heating':
            is_supply = 'is_supply_heating'
            nodelist = self.nodelists_heating[network_id]
        elif network_type == 'cooling':
            is_supply = 'is_supply_cooling'
            nodelist = self.nodelists_cooling[network_id]

        supplies = []
        for node in self.nodelist_building:
            if self.nodes[node][is_supply] is True:
                supplies.append(node)

        accept = False
        counter = 0
        while not accept and counter <= max_iter:
            counter += 1
            curr_removed = []
            for node in nodelist:
                connected = False
                for supply in supplies:
                    if nx.has_path(self, node, supply):
                        connected = True
                if connected is False:
                    if 'name' in self.nodes[node]:
                        curr_removed.append(self.nodes[node]['name'])
                    else:
                        curr_removed.append(node)
                    self.remove_network_node(node)

            if len(curr_removed) == 0:
                accept = True
            else:
                for node in curr_removed:
                    if node not in removed:
                        removed.append(node)

        if counter == max_iter:
            warnings.warn('Reached maximum number of iterations')

        return removed

    def remove_self_edges(self, network_type, network_id='default'):
        """The network may contain edges with length 0 m that should be removed

         Parameters
        ----------
        network_type : str
            Specifies the type of the network as {'heating', 'cooling',
            'electricity', 'gas', 'others'}
        network_id : str
            Name of the network

        Returns
        -------
        number_removed_edges : int
            Number of removed network edges
        """
        number_removed_edges = 0
        to_remove = []
        for edge in self.edges():
            if self.edges[edge[0], edge[1]]['length'] <= 1e-9:
                if edge[0] == edge[1]:
                    to_remove.append([edge[0], edge[1]])
                    
        for edge in to_remove:
            self.remove_edge(edge[0], edge[1])
            number_removed_edges += 1

        return number_removed_edges

    def remove_dead_ends(self, network_type, network_id='default'):
        """Removes any nodes and edges that lead to dead ends in the network

        Parameters
        ----------
        network_type : str
            Specifies the type of the network as {'heating', 'cooling',
            'electricity', 'gas', 'others'}
        network_id : str
            Name of the network

        Returns
        -------
        removed : list
            Names of removed network nodes
        """
        removed = []

        if network_type == 'heating':
            nodelist = self.nodelists_heating[network_id]
        elif network_type == 'cooling':
            nodelist = self.nodelists_cooling[network_id]

        def remove_end(end):
            """Deletes a dead end and follows up on its neighbor for recursion

            Parameters
            ----------
            end : int
                Node number of the dead end
            """
            neighbor = list(nx.neighbors(self, end))
            if neighbor != []:
                if nx.degree(self, neighbor[0]) <= 2:
                    if 'name' in self.nodes[end]:
                        removed.append(self.nodes[end]['name'])
                    else:
                        removed.append(end)
                    self.remove_network_node(end)
                    remove_end(neighbor[0])
                else:
                    if 'name' in self.nodes[end]:
                        removed.append(self.nodes[end]['name'])
                    else:
                        removed.append(end)
                    self.remove_network_node(end)

        dead_ends = []
        for node in nodelist:
            if 'network' in self.nodes[node]['node_type']:
                if nx.degree(self, node) == 1:
                    dead_ends.append(node)

        for end in dead_ends:
            remove_end(end)

        return removed

    def calc_angle(self, a, b, output='rad'):
        """Returns the angle of a line from point a to b in rad or degrees

        Parameters
        ----------
        a : shapely.geometry.point object
        b : shapely.geometry.point object
        output : str
            Selection of output unit between 'rad' and 'degrees'

        Returns
        -------
        angle : float
            Angle of a line from point a to b in rad or degrees
        """
        assert output in ['rad', 'degrees'], 'Output must be rad or degrees'

        angle = math.atan2(b.y - a.y, b.x - a.x)
        if angle < 0:
            angle = 2 * math.pi + angle
        if output == 'degrees':
            angle_degrees = (angle) * 360 / (2*math.pi)
            return angle_degrees
        else:
            return angle
