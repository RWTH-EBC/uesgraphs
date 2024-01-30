# -*- coding: utf-8 -*-
# @Author: MichaMans
# @Date:   2019-05-08 16:58:52
# @Last Modified by:   MichaMans
# @Last Modified time: 2021-08-09 15:26:00

import pandas as pd
import numpy as np
import shapely.geometry as sg
from sklearn.cluster import DBSCAN
from random import randint

import shapely.ops as ops
import pyproj
from functools import partial

import networkx as nx
import math
import warnings


def cluster_bldg(uesgen, eps=20):
    """Cluster demand buildings geographically.

    Parameters
    ----------
    eps : int
        max distance (in m) that points can be away from each other to
        be considered a cluster
    """
    coords_dict = {"x": [], "y": [], "node": []}
    for node in uesgen.uesgraph.nodelist_building:
        if not uesgen.uesgraph.nodes[node]["is_supply_heating"]:
            coords_dict["x"].append(uesgen.uesgraph.nodes[node]["position"].x)
            coords_dict["y"].append(uesgen.uesgraph.nodes[node]["position"].y)
            coords_dict["node"].append(node)

    coords_df = pd.DataFrame(data=coords_dict)
    coords = coords_df.iloc[:, 0:2].values

    db = DBSCAN(eps=eps, min_samples=1).fit(coords)
    cluster_labels = [x for x in db.labels_]
    num_clusters = len(set(cluster_labels))
    print("Number of cluster: {} (before: {} coords)".format(num_clusters, len(coords)))

    clusters = {}
    for i, cluster_label in enumerate(cluster_labels):
        if cluster_label not in clusters:
            clusters[cluster_label] = [coords_dict["node"][i]]
        else:
            clusters[cluster_label].append(coords_dict["node"][i])

    cluster_names = []
    for cluster in clusters.keys():
        if len(clusters[cluster]) > 1:
            xs = []
            ys = []
            input_heat = {}
            for node in clusters[cluster]:
                xs.append(uesgen.uesgraph.nodes[node]["position"].x)
                ys.append(uesgen.uesgraph.nodes[node]["position"].y)
                if "input_heat" in uesgen.uesgraph.nodes[node]:
                    input_heat[node] = uesgen.uesgraph.nodes[node]["input_heat"]

            x_mean = np.mean(xs)
            y_mean = np.mean(ys)
            _err = np.inf
            for i, (_x, _y) in enumerate(zip(xs, ys)):
                err = (_x - x_mean) ** 2 + (_y - y_mean) ** 2
                if err < _err:
                    _err = err
                    x = _x
                    y = _y
                    node_before = clusters[cluster][i]

            cl_name = "Cluster{}".format(cluster)

            if input_heat:
                input_heat = pd.DataFrame(input_heat).sum(axis=1).values.tolist()
                uesgen.uesgraph.add_building(
                    name=cl_name, position=sg.Point(x, y), input_heat=input_heat
                )
            else:
                uesgen.uesgraph.add_building(name=cl_name, position=sg.Point(x, y))
            edges_to_add = []
            cluster_node = uesgen.uesgraph.nodes_by_name[cl_name]
            for i, edge in enumerate(uesgen.uesgraph.edges):
                if edge[0] == node_before:
                    edges_to_add.append([edge[1], cluster_node])

                elif edge[1] == node_before:
                    edges_to_add.append([edge[0], cluster_node])

            cluster_names.append(cl_name)
            for edge in edges_to_add:
                uesgen.uesgraph.add_edge(edge[0], edge[1], name=randint(0, 10000000))

            for node in clusters[cluster]:
                uesgen.uesgraph.remove_building(node)

    return uesgen


def guess_year_of_construction(distribution="destatis"):
    """Return a random year of construction from given `distribution`.

    Datasource `'destatis'` is taken from DENA Gebaeudereport 2015, p.31
    https://shop.dena.de/sortiment/detail/?tx_zrwshop_pi1[pid]=552

    Parameters
    ----------
    distribution : str
        Chooses one of the implemented datasources for the distributions
        of construction years. Currently, {'destatis'} is the only
        implemented data source

    Returns
    -------
    year_of_construction : int
        Random guess for a building's year of construction
    """
    if distribution == "destatis":
        random_decision = np.random.uniform(0, 1)
        if random_decision <= 0.13:
            year_of_construction = np.random.choice(range(1900, 1919))
        elif random_decision <= 0.13 + 0.12:
            year_of_construction = np.random.choice(range(1919, 1949))
        elif random_decision <= 0.13 + 0.12 + 0.38:
            year_of_construction = np.random.choice(range(1949, 1979))
        elif random_decision <= 0.13 + 0.12 + 0.38 + 0.14:
            year_of_construction = np.random.choice(range(1979, 1991))
        elif random_decision <= 0.13 + 0.12 + 0.38 + 0.14 + 0.14:
            year_of_construction = np.random.choice(range(1991, 2001))
        elif random_decision <= 0.13 + 0.12 + 0.38 + 0.14 + 0.14 + 0.07:
            year_of_construction = np.random.choice(range(2001, 2009))
        else:
            now = datetime.datetime.now()
            year_of_construction = np.random.choice(range(2009, now.year))

    return year_of_construction


def add_years_of_construction(uesgen, all_buildings=True):
    """Add guess values for all buildings' years of construction.

    Parameters
    ----------
    all_buildings : boolean
        If `all_buildings is True`, values will be added to all
        buildings in the graph. Else, values will only be assigned to
        buildings connected to the current network

    Returns
    -------
    uesgen : object
        A uesgenerator object with the enriched information
    construction_years : dict
        A dict with building node number as key and year of construction
        as value
    """
    construction_years = {}
    if all_buildings is True:
        nodelist = uesgen.uesgraph.nodelist_building
    else:
        nodelist = uesgen.connected_nodes

    for building in nodelist:
        if uesgen.uesgraph.node[building]["is_supply_heating"] is False:
            uesgen.uesgraph.node[building][
                "year_of_construction"
            ] = guess_year_of_construction()
            construction_years[building] = uesgen.uesgraph.node[building][
                "year_of_construction"
            ]

    return uesgen, construction_years


def add_floor_heights(uesgen, floor_height=None, all_buildings=True):
    """Add given values for floor heights. Default value is 3 m.

    Parameters
    ----------
    floor_height : float
        Height of each floor in the building for TEASER modeling
    all_buildings : boolean
        If `all_buildings is True`, values will be added to all
        buildings in the graph. Else, values will only be assigned to
        buildings connected to the current network

    Returns
    -------
    uesgen : object
        A uesgenerator object with the enriched information
    """
    if floor_height is None:
        floor_height = 3.0
    else:
        assert isinstance(
            floor_height, type(3.0)
        ), "floor_height should\
            be of type float"

    if all_buildings is True:
        nodelist = uesgen.uesgraph.nodelist_building
    else:
        nodelist = uesgen.connected_nodes

    for building in nodelist:
        if uesgen.uesgraph.node[building]["is_supply_heating"] is False:
            uesgen.uesgraph.node[building]["floor_height"] = floor_height

    return uesgen


def add_number_of_floors(uesgen, max_floors=None, all_buildings=True):
    """Add guess values for number_of_floors.

    This will pick a number of floors between 1 and `max_floors`,
    which by default is 3.

    Parameters
    ----------
    max_floors : int
        Maximum number of floors to randomly pick from
    all_buildings : boolean
        If `all_buildings is True`, values will be added to all
        buildings in the graph. Else, values will only be assigned to
        buildings connected to the current network

    Returns
    -------
    uesgen : object
        A uesgenerator object with the enriched information
    """
    if max_floors is None:
        max_floors = 3
    else:
        assert isinstance(max_floors, type(3)), "max_floors should be " "of type int"

    if all_buildings is True:
        nodelist = uesgen.uesgraph.nodelist_building
    else:
        nodelist = uesgen.connected_nodes

    for building in nodelist:
        if uesgen.uesgraph.node[building]["is_supply_heating"] is False:
            uesgen.uesgraph.node[building]["number_of_floors"] = np.random.choice(
                range(1, max_floors + 1)
            )

    return uesgen


# old functions revision need or be deleted


########################
# Methods for review after shapely integration


def add_pv(self, share_pv):
    """Convert a given share of buildings to electricity suppliers.

    Parameters
    ----------

    share_pv : float
        Must be between 0.0 and 1.0

    Returns
    -------

    nodelist_pv : list
        List of all building nodes that have been converted to electricity
        supplies
    """
    assert share_pv >= 0.0 and share_pv <= 1.0, "share_pv not between 0 and 1"
    nodelist_pv = []
    if share_pv > 0.0:
        no_buildings = len(self.uesgraph.nodelist_building)
        no_buildings_pv = round(no_buildings * float(share_pv), 0)

        if share_pv < 0.4:
            while len(nodelist_pv) < no_buildings_pv:
                building = random.choice(self.uesgraph.nodelist_building)
                if self.uesgraph.node[building]["is_supply_electricity"] is False:
                    self.uesgraph.node[building]["is_supply_electricity"] = True
                    nodelist_pv.append(building)
        elif share_pv == 1.0:
            for building in self.uesgraph.nodelist_building:
                self.uesgraph.node[building]["is_supply_electricity"] = True
                nodelist_pv.append(building)
        else:
            for building in self.uesgraph.nodelist_building:
                self.uesgraph.node[building]["is_supply_electricity"] = True
                nodelist_pv.append(building)
            while len(nodelist_pv) > no_buildings_pv:
                building = random.choice(self.uesgraph.nodelist_building)
                if self.uesgraph.node[building]["is_supply_electricity"] is True:
                    self.uesgraph.node[building]["is_supply_electricity"] = False
                    nodelist_pv.remove(building)

    return nodelist_pv


def add_loop(graph):
    """Add a loop to the network if there is still room for one.

    Returns
    -------

    loop_edges : list
        Edges closing loops
    """
    loop_counter = 0
    loop_edges = []
    if loop_counter >= len(graph.block_corners.keys()):
        print("No blocks left to add loops")
    else:
        degree_candidates = {}
        candidates = {}
        possible_edges = {}

        for block in graph.street_corners.keys():
            degree_candidates[block] = []
            candidates[block] = []
            possible_edges[block] = {}
            for node in graph.block_nodes[block]:
                if graph.uesgraph.degree(node) == 2:
                    degree_candidates[block].append(node)

            for degree_candidate in degree_candidates[block]:
                candidates[block].append(degree_candidate)
            for corner in graph.block_corners[block]:
                candidates[block].append(corner)

            for candidate_0 in candidates[block]:
                for candidate_1 in candidates[block]:
                    if candidate_0 != candidate_1:
                        path_len = len(
                            nx.shortest_path(graph.uesgraph, candidate_0, candidate_1)
                        )
                        if path_len not in possible_edges[block].keys():
                            possible_edges[block][path_len] = []
                        if [candidate_1, candidate_0] not in possible_edges[block][
                            path_len
                        ]:
                            possible_edges[block][path_len].append(
                                [candidate_0, candidate_1]
                            )
            loop_edge = possible_edges[block][max(possible_edges[block].keys())][0]
            loop_edges.append(loop_edge)

        print("loop_edges:", loop_edges)

        curr_loop_edge = loop_edges[loop_counter]
        print("Add loop through edge", curr_loop_edge)
        graph.uesgraph.add_edge(curr_loop_edge[0], curr_loop_edge[1])

        diameters = []
        for edge_node in curr_loop_edge:
            neighbors = graph.uesgraph.neighbors(edge_node)
            to_remove = []
            for neighbor in neighbors:
                if neighbor in curr_loop_edge:
                    to_remove.append(neighbor)
                if neighbor in graph.uesgraph.nodelist_building:
                    to_remove.append(neighbor)
            for remove_me in to_remove:
                neighbors.remove(remove_me)
            print("~~~~~")
            print("Trying", edge_node, neighbors[0])
            if "diameter_heating" in graph.uesgraph.edge[edge_node][neighbors[0]]:
                diameters.append(
                    graph.uesgraph.edge[edge_node][neighbors[0]]["diameter_heating"]
                )
            else:
                diameters.append(0.1)
        curr_diameter = (diameters[0] + diameters[1]) / 2
        graph.uesgraph.edge[curr_loop_edge[0]][curr_loop_edge[1]][
            "diameter_heating"
        ] = curr_diameter
        print(
            "~~~~~~",
            "graph.uesgraph.edge[curr_loop_edge[0]][curr_loop_edge[1]]",
            graph.uesgraph.edge[curr_loop_edge[0]][curr_loop_edge[1]],
        )

    loop_counter += 1

    return graph, loop_edges


# This function will be added to the uesmodels object


def size_hydronic_network(
    graph,
    network_type,
    delta_t_heating=20.0,
    delta_t_cooling=6.0,
    dp_set=80.0,
    loop=False,
    diameters_list=None
):
    """Calculate diameters of hydronic network with given nodelist.

    Consumption nodes in `graph.uesgraphs` should have an attribute
    `'max_demand_' + network_type` (e.g. `max_demand_heating`) to calculate
    pipe diameters accordingly.

    So far, this only marks the paths of each max_demand.

    Parameters
    ----------

    network_type : str
        {'heating', 'cooling'}
    delta_t_heating : float
        Design temperature difference between supply and return for a
        heating network
    delta_t_cooling : float
        Design temperature difference between supply and return for a
        cooling network
    dp_set : float
        Specific design pressure drop for pipe network in Pa/m
    diameters_list : list
        Contains diameters which algorithm can choose from in m
    """
    assert network_type in ["heating", "cooling"], "Unknown network"

    if diameters_list is not None:
        diameters = diameters_list
    else:
        diameters = [
            0.015,
            0.02,
            0.025,
            0.032,
            0.04,
            0.05,
            0.065,
            0.08,
            0.1,
            0.125,
            0.15,
            0.2,
            0.25,
            0.3,
            0.35,
            0.4,
            0.45,
            0.5,
            0.6,
            0.7,
            0.8,
            0.9,
            1.0,
            1.1,
            1.2,
        ]

    network_type = "heating"
    subgraph = graph.create_subgraphs("heating")["default"]

    supplies = []
    for node in graph.nodelist_building:
        if graph.node[node]["is_supply_" + network_type] is True:
            supplies.append(node)
    supply = supplies[0]  # Currently only 1 supported supply per network

    edgelist = []
    for node in graph.nodelist_building:
        if graph.node[node]["is_supply_" + network_type] is False:
            if "max_demand_" + network_type in graph.node[node]:
                path = nx.shortest_path(subgraph, supply, node)
                max_demand = graph.node[node]["max_demand_" + network_type]
                for i in range(len(path) - 1):
                    node_0 = path[i]
                    node_1 = path[i + 1]
                    if "max_demand_" + network_type in graph.edges[node_0, node_1]:
                        graph.edges[node_0, node_1][
                            "max_demand_" + network_type
                        ] += max_demand
                    else:
                        graph.edges[node_0, node_1][
                            "max_demand_" + network_type
                        ] = max_demand
                    edgelist.append([node_0, node_1])
            else:
                raise ValueError(
                    "No maximum demand for the building node is defined!"
                    + "No Diameter can be evaluated")
                break

    # Calculate nominal mass flow rates according to maximum demand

    if network_type == "heating":
        dT = delta_t_heating
    elif network_type == "cooling":
        dT = delta_t_cooling
    for edge in edgelist:
        max_demand = graph.edges[edge[0], edge[1]]["max_demand_" + network_type]
        cp = 4180  # J/(kg*K)
        m_flow = max_demand / (cp * dT)
        graph.edges[edge[0], edge[1]]["m_flow_" + network_type] = m_flow

    # Calculate pressure drops and assign diameter
    for edge in edgelist:
        m_flow = graph.edges[edge[0], edge[1]]["m_flow_" + network_type]
        dp_spec = 1e99  # Pa/m
        i = 0
        while dp_spec > dp_set:
            diameter = diameters[i]
            dp_spec = 8 * 0.025 / (diameter ** 5 * math.pi ** 2 * 983) * m_flow ** 2
            i += 1
        graph.edges[edge[0], edge[1]]["diameter"] = diameter

    if loop:
        for edge in graph.edges():
            if "diameter" not in graph.edges[edge[0], edge[1]].keys():

                for ed in graph.edges(edge[0]):
                    if "diameter" in graph.edges[ed]:
                        diameter = graph.edges[ed]["diameter"]
                        break
                graph.edges[edge]["diameter"] = diameter

    return graph


def transform_to_new_coordination_system(graph, streets=None):
    # Transform to new coordinate system
    new_min = latlon2abs(graph.min_position, graph.min_position.y, graph.max_position.y)
    new_max = latlon2abs(graph.max_position, graph.min_position.y, graph.max_position.y)

    for node in graph.nodes():
        new_position = latlon2abs(
            graph.nodes[node]["position"], graph.min_position.y, graph.max_position.y
        )
        new_x = new_position.x - new_min.x
        new_y = new_position.y - new_min.y

        graph.nodes[node]["position"] = sg.Point(new_x, new_y)

    if streets:
        transformed_streets = []
        for street in streets:
            transformed_street = latlon2abs(
                street, graph.min_position.y, graph.max_position.y
            )
            to_line_string = []
            for point in transformed_street.coords:
                to_line_string.append(
                    sg.Point(point[0] - new_min.x, point[1] - new_min.y)
                )

            transformed_streets.append(sg.LineString(to_line_string))

        streets = transformed_streets
        graph.graph["streets"] = streets
        graph.graph["transformed"] = True

    graph.min_position = None
    graph.max_position = None

    for node in graph.nodes():
        graph._update_min_max_positions(graph.nodes[node]["position"])

    return graph


def latlon2abs(geometry, lat1, lat2):
    """Convert a geometry object from lat/lon to absolute coords.

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
    proj_4326_crs = pyproj.crs.CRS("epsg:4326")
    proj_from_latlat_crs = pyproj.crs.CRS(proj="aea", lat_1=lat1, lat_2=lat2)
    transformer = pyproj.Transformer.from_crs(
        proj_4326_crs,
        proj_from_latlat_crs,
        always_xy=True).transform

    converted = ops.transform(transformer, geometry)

    return converted
