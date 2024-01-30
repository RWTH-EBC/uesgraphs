# -*- coding:utf8 -*-
"""This module contains the District class to describe the UES.

Example can be found in:

    - e9_generate_ues_from_osm.py
"""

import os
import networkx as nx
import random
import math
import shapely.geometry as sg
import shapely
from functools import partial
import shapely.ops as ops
import pyproj
import datetime
from shapely.ops import cascaded_union
import uesgraphs as ug
from shapely.prepared import prep
import uesgraphs.visuals as visuals


class UESGenerator(object):
    """
    Generator for random urban energy system use cases.

    Attributes
    ----------

    uesgraph : uesgraphs.district.District() object
        Default empty uesgraph into which the use case is generated
    street_corners : dict
        A dictionary with block numbers as keys and lists of street nodes for
        this block as corresponding values. Thus, a list of street nodes can
        be easily retrieved for each block.
    block_corners : dict
        A dictionary with block numbers as keys and lists of network nodes on
        corners for this block as corresponding values.
    block_nodes : dict
        A dictionary with block numbers as keys and lists of network nodes for
        this block as corresponding values.
    rejected_choices : list
        Nodes from which to extend the street network for a new block are
        chosen randomly. If a node has already been rejected once because it is
        not suitable to start a new block from it, it is appended to this list.
        Thus, it does not need to be considered again.
    loop_counter : int
        Counts the number of loops that have been added to the network.

    network_line : shapely.geometry.MultiLineString object
        The currently filled network as shapely line strings
    streets : list
        List of streets as shapely LineString objects. Not a complete list of
        all streets (would possibly be computationally expensive to create),
        but a list of streets as used so far in generation
    crossings : list
        A list of all node numbers that represent a street crossing
    connected_nodes : list
        A list of all nodes that have been connected to the network by
        generator
    """

    def __init__(self):
        """Constructor for UESGenerator class."""
        self.uesgraph = ug.UESGraph()
        self.street_corners = {}
        self.block_corners = {}
        self.block_nodes = {}
        self.rejected_choices = []
        self.loop_counter = 0

        self.network_line = sg.LineString()
        self.streets = []
        self.crossings = []
        self.connected_nodes = []

    def find_crossings(self):
        """Find all street crossings in street network and creates streets."""
        for street_node in self.uesgraph.nodelist_street:
            if self.uesgraph.degree(street_node) > 2:
                self.crossings.append(street_node)
            elif self.uesgraph.degree(street_node) == 1:
                self.crossings.append(street_node)

    def find_in_proximity(self, nodes, searched_type):
        """Find the closest elements of `searched_type` to `nodes`.

        Parameters
        ----------
        nodes : list
            List of node numbers for nodes to which search element should be
            close. Alternatively, the list may contain
            shapely.geometry.Point objects.
        searched_type : str
            {'street', 'building', 'street_node'}

        Returns
        -------
        close_elements : list
            A list of closest elements of `searched_type`
        """
        close_elements = []
        radius = 0
        counter = 0
        start_positions = []
        for node in nodes:
            if isinstance(node, type(sg.Point())):
                start_positions.append(node)
            else:
                start_positions.append(self.uesgraph.node[node]["position"])
        while len(close_elements) < 1 and counter < 20:
            counter += 1
            radius += (self.uesgraph.max_position.x - self.uesgraph.min_position.x) / 40
            buffers = []
            for start_position in start_positions:
                buffers.append(start_position.buffer(radius))

            proximity = cascaded_union(buffers)
            prepared_proximity = prep(proximity)

            if searched_type == "street":
                for street in self.uesgraph.graph["streets"]:
                    if street.intersects(proximity):
                        close_elements.append(street)
                for street in self.streets:
                    if street.intersects(proximity):
                        close_elements.append(street)
            elif searched_type == "building":
                self.uesgraph.graph["proximity"] = proximity
                for building in self.uesgraph.nodelist_building:
                    if building not in self.rejected_choices:
                        if self.uesgraph.node[building]["is_supply_heating"] is False:
                            position = self.uesgraph.node[building]["position"]
                            if proximity.contains(position):
                                close_elements.append(building)
            elif searched_type == "street_node":
                for street_node in self.uesgraph.nodelist_street:
                    position = self.uesgraph.node[street_node]["position"]
                    if proximity.contains(position):
                        close_elements.append(street_node)

        return close_elements

    def connect_node_to_network(self, building_node, log):
        """Connect a building to the street network.

        Buildings are located near the existing street network. This method
        adds a street node `street_node_0` in direct vicinity of the building
        node and  connects `street_node_0` to the street network on the
        intersection node `street_node_1`. In addition, a heating node
        `heating_node` is placed on the same position as `street_node_0`.
        `heating_node` is connected to the building to form the heating
        network connection. The method returns `street_node_0`, from where
        the heat network connection can be extended in subsequent methods.

        Parameters
        ----------
        building_node : int
            Node number of node to be connected
        log : open(file) object
            Log file for development

        Returns
        -------
        street_node_0 : int
            Node number of newly created street node for `building_node`
        """
        start_position = self.uesgraph.node[building_node]["position"]

        # Find all streets close to the building node
        close_streets = self.find_in_proximity([building_node], "street")

        # Find `projection`, which is the point object representing the
        # projection of the building node onto the street network
        distance_streets = {}  # {<distance to start point>: <new point>}
        for street in close_streets:
            new_point = street.interpolate(street.project(start_position))
            distance = new_point.distance(start_position)
            distance_streets[distance] = street

        closest_street = distance_streets[min(distance_streets.keys())]
        projection = closest_street.interpolate(closest_street.project(start_position))

        # Find `closest_street_node`, which is the street node closest to
        # `projection`
        close_street_nodes = self.find_in_proximity([projection], "street_node")

        closest_street_node = self.find_closest_node(projection, close_street_nodes)

        # Check whether `projection` is on `closest_street_node` or in
        # between `closest_street_node` and one of its neighbors
        closest_street_position = self.uesgraph.node[closest_street_node]["position"]
        if projection.almost_equals(closest_street_position):
            street_node_1 = closest_street_node
        else:
            # Next, find `closest_street_node`'s correct neighbor
            neighbors = self.uesgraph.neighbors(closest_street_node)
            distances_neighbors = {}
            for neighbor in neighbors:
                log.write("CHECKING NEIGHBOR {}\n".format(neighbor))
                neighbor_position = self.uesgraph.node[neighbor]["position"]
                line = sg.LineString([closest_street_position, neighbor_position])
                distances_neighbors[neighbor] = projection.distance(line)
                log.write("DISTANCES ARE {}\n".format(distances_neighbors))
            neighbor_node = min(distances_neighbors, key=distances_neighbors.get)

            # Create a new street node at `projection` and insert it in
            # between `closest_street_node` and its `neighbor`
            street_node_1 = self.uesgraph.add_street_node(
                projection, check_overlap=False
            )
            self.uesgraph.remove_edge(closest_street_node, neighbor_node)
            self.uesgraph.add_edge(closest_street_node, street_node_1)
            self.uesgraph.add_edge(neighbor_node, street_node_1)

            # If there was already a heating connection on top of the two
            # street nodes `closest_street_node` and `neighbor_node` before
            # the insertion, this connection should also be inserted with a
            # new heating node
            if (
                "corresp_hn" in self.uesgraph.node[closest_street_node]
                and "corresp_hn" in self.uesgraph.node[neighbor_node]
            ):
                hn_1 = self.uesgraph.node[closest_street_node]["corresp_hn"]
                hn_2 = self.uesgraph.node[neighbor_node]["corresp_hn"]
                if hn_2 in self.uesgraph.neighbors(hn_1):
                    new_hn = self.uesgraph.add_network_node(
                        "heating", position=projection, check_overlap=False
                    )
                    self.uesgraph.node[new_hn]["corresp_sn"] = street_node_1
                    self.uesgraph.node[street_node_1]["corresp_hn"] = new_hn
                    self.uesgraph.remove_edge(hn_1, hn_2)
                    self.uesgraph.add_edge(hn_1, new_hn)
                    self.uesgraph.add_edge(hn_2, new_hn)

        # Add a street from `street_node_1` at the position
        # `projection` almost until `building_node`
        new_line = sg.LineString([projection, start_position])
        near_building = new_line.interpolate(0.9)

        street_node_0 = self.uesgraph.add_street_node(
            near_building, check_overlap=False
        )
        self.uesgraph.add_edge(street_node_0, street_node_1)
        self.streets.append(sg.LineString([projection, near_building]))

        # Add a heating node at `near_building` and connect it to
        # `building_node`
        heating_node = self.uesgraph.add_network_node(
            "heating", position=near_building, check_overlap=False
        )
        self.uesgraph.node[heating_node]["corresp_sn"] = street_node_0
        self.uesgraph.node[street_node_0]["corresp_hn"] = heating_node
        self.uesgraph.add_edge(heating_node, building_node)

        return street_node_0

    def find_closest_node(self, node, nodelist):
        """Find the closest node withing the nodelist.

        Parameters
        ----------
        node : int
            Node number from where the closest node should be found
        nodelist : list
            list of nodes to look after the closest one

        Returns
        -------
        closest_node : int
            Node number of the closest node
        """
        if isinstance(node, type(sg.Point())):
            start_position = node
        else:
            start_position = self.uesgraph.node[node]["position"]
        distances = {}
        for other_node in nodelist:
            if other_node != node:
                other_position = self.uesgraph.node[other_node]["position"]
                distances[other_node] = start_position.distance(other_position)
        closest_node = min(distances, key=distances.get)
        return closest_node

    def add_network_new(
        self, supply_node, number_of_buildings, success_rate, workspace
    ):
        """Add a heating network to the district.

        Parameters
        ----------
        supply_node : int
            Node number of supply node
        number_of_buildings : int
            Number of buildings to be connected to the heating network
        success_rate : float
            Probability of a building to be part of the heating network

        Returns
        -------
        self.uesgraph : uesgraph object
            District with buildings, streets, and heat network
        """
        open(os.path.join(workspace, "network_log.txt"), "w").close()
        log = open(os.path.join(workspace, "network_log.txt"), "w")
        performance_timing = []
        start_networking = datetime.datetime.now()

        # Start log file for network generation
        log.write("Starting at supply node {}\n".format(supply_node))

        # Start network by connecting the supply to the street network
        self.connected_nodes.append(supply_node)
        street_node_0 = self.connect_node_to_network(supply_node, log)

        # Assert a correct street network
        is_network_ok = True
        nodes_unconnected = []
        for node in self.uesgraph.nodelist_street:

            if not nx.has_path(self.uesgraph, node, street_node_0):
                nodes_unconnected.append(node)
                is_network_ok = False

        if not is_network_ok:

            save_as = os.path.join(workspace, "broken.png")

            vis = ug.Visuals(self.uesgraph)
            vis.show_network(
                save_as=save_as,
                show_plot=False,
                show_diameters=False,
                scaling_factor=10,
                scaling_factor_diameter=40,
                simple=False,
                edge_markers=[],
                node_markers=nodes_unconnected,
            )

            for node in nodes_unconnected:
                self.uesgraph.remove_street_node(node)

            save_as = os.path.join(workspace, "broken-removed.png")
            vis.show_network(
                save_as=save_as,
                show_plot=False,
                show_diameters=False,
                scaling_factor=10,
                scaling_factor_diameter=40,
                simple=False,
                edge_markers=[],
                node_markers=[],
            )
            # msg = "{} street nodes are not connected".format(
            #     len(nodes_unconnected))
            # raise ValueError(msg.format(node))

        print("Street network is OK")

        # Start the process of connecting the buildings to the new network
        counter = 0
        while len(self.connected_nodes) - 1 < number_of_buildings:
            counter += 1

            # Find a next building close to the existing network
            hns = self.uesgraph.nodelists_heating["default"]
            accept_building = False
            while accept_building is False:
                close_buildings = self.find_in_proximity(
                    self.connected_nodes + hns, "building"
                )
                try:
                    closest_building = self.find_closest_node(
                        supply_node, close_buildings
                    )
                except:
                    save_as = os.path.join(
                        workspace, "cannot_connect" + str(counter) + ".png"
                    )
                    vis = ug.Visuals(self.uesgraph)
                    vis.show_network(save_as=save_as, show_plot=False, simple=True)

                random_decision = random.uniform(0, 1)
                if random_decision <= success_rate or counter == 1:
                    accept_building = True
                else:
                    self.rejected_choices.append(closest_building)

            # Connect the building to a new heating node on the street network
            street_node_1 = self.connect_node_to_network(closest_building, log)
            self.connected_nodes.append(closest_building)
            self.rejected_choices.append(closest_building)

            # Find heating network's node that is closest to the new
            # building to make a new network connection
            omit = [self.uesgraph.node[street_node_1]["corresp_hn"]]
            network_node_0 = self.find_closest_node(
                closest_building, list(set(hns) - set(omit))
            )

            street_node_0 = self.uesgraph.node[network_node_0]["corresp_sn"]

            # Find the shortest path between the street nodes that connect the
            # supply and the new building onto the street network
            log.write(
                "Finding path between {} and {}\n".format(street_node_0, street_node_1)
            )

            try:
                curr_path = nx.shortest_path(
                    self.uesgraph, street_node_0, street_node_1
                )
            # to Do: revision needed
            except:

                save_as = os.path.join(
                    workspace, "cannot_connect" + str(counter) + ".png"
                )
                vis = ug.Visuals(self.uesgraph)
                vis.show_network(save_as=save_as, show_plot=False, simple=True)

            # Make a heat network connection along the street path between the
            # two existing heating nodes
            hn_0 = self.uesgraph.node[curr_path[0]]["corresp_hn"]
            for sn_1 in curr_path[1:]:
                if "corresp_hn" in self.uesgraph.node[sn_1]:
                    hn_1 = self.uesgraph.node[sn_1]["corresp_hn"]
                    if hn_1 not in self.uesgraph.neighbors(hn_0):
                        self.uesgraph.add_edge(hn_0, hn_1)
                    hn_0 = hn_1
                else:
                    sn_1_pos = self.uesgraph.node[sn_1]["position"]
                    new_hn = self.uesgraph.add_network_node(
                        "heating", position=sn_1_pos, check_overlap=False
                    )
                    self.uesgraph.node[new_hn]["corresp_sn"] = sn_1
                    self.uesgraph.node[sn_1]["corresp_hn"] = new_hn
                    self.uesgraph.add_edge(hn_0, new_hn)
                    hn_0 = new_hn

            performance_timing.append(
                (datetime.datetime.now() - start_networking).total_seconds()
            )

            # save_as = os.path.join(workspace, '10_build_' + str(counter) +
            #     '.png')
            # vis = ug.Visuals(self.uesgraph)
            # vis.show_network(save_as=save_as, show_plot=False, simple=True)

        # Clear unnecessary pipes from the network
        for building in self.connected_nodes:
            curr_path = nx.shortest_path(self.uesgraph, building, supply_node)
            for i in range(1, len(curr_path)):
                self.uesgraph.edges[curr_path[i - 1], curr_path[i]]["used"] = True
        edges_to_remove = []
        for edge in self.uesgraph.edges():
            if (
                "corresp_sn" in self.uesgraph.node[edge[0]]
                and "corresp_sn" in self.uesgraph.node[edge[1]]
            ):
                if "used" not in self.uesgraph.edges[edge[0], edge[1]]:
                    edges_to_remove.append(edge)
                    # self.uesgraph.remove_edge(edge[0], edge[1])
                    if "removed_edges" in self.uesgraph.graph:
                        self.uesgraph.graph["removed_edges"].append(edge)
                    else:
                        self.uesgraph.graph["removed_edges"] = [edge]
            if len(list(self.uesgraph.neighbors(edge[0]))) == 0:
                sn_0 = self.uesgraph.node[edge[0]]["corresp_sn"]
                self.uesgraph.remove_network_node(edge[0])
                del self.uesgraph.node[sn_0]["corresp_hn"]
            if len(list(self.uesgraph.neighbors(edge[1]))) == 0:
                sn_1 = self.uesgraph.node[edge[1]]["corresp_sn"]
                self.uesgraph.remove_network_node(edge[1])
                del self.uesgraph.node[sn_1]["corresp_hn"]

        for edge in edges_to_remove:
            self.uesgraph.remove_edge(edge[0], edge[1])

        for building in self.connected_nodes:
            assert len(list(self.uesgraph.neighbors(building))) > 0

        log.close()
        self.uesgraph.graph["timing"] = performance_timing
        return self.uesgraph

    def find_nearest_node(self, origin, node_type):
        """Return the nearest node to `origin` of a given `node_type`.

        Parameters
        ----------
        origin : shapely.geometry.Point object
            Origin to compare distances to
        node_type : str
            {'street', 'building'}

        Returns
        -------
        nearest_node : int
            Node number of the nearest node
        """
        func_time = datetime.datetime.now()
        supply_position = self.uesgraph.node[origin]["position"]
        distances = {}
        if node_type == "street":
            candidate_nodes = self.uesgraph.nodelist_street
        if node_type == "building":
            candidate_nodes = self.uesgraph.nodelist_building
        for candidate_node in candidate_nodes:
            curr_position = self.uesgraph.node[candidate_node]["position"]
            distances[candidate_node] = supply_position.distance(curr_position)

        accept = False
        while accept is False:
            accept = True
            nearest_node = min(distances, key=distances.get)
            for neighbor in self.uesgraph.neighbors(nearest_node):
                if "heat" in self.uesgraph.node[neighbor]["node_type"]:
                    accept = False
                    del distances[nearest_node]

        return nearest_node
