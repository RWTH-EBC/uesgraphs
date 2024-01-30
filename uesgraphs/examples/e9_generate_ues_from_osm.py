# -*- coding: utf-8 -*-
# @Author: MichaMans
# @Date:   2019-03-12 08:26:20
# @Last Modified by:   MichaMans
# @Last Modified time: 2021-08-09 11:42:33

import os
from shapely.geometry import Point
import uesgraphs as ug
import uesgraphs.uesmodels.utilities.uesgenerator as uesgen
import uesgraphs.uesmodels.utilities.utilities as utils
import networkx as nx
import uesgraphs.utilities as ut


def main():
    """Main function."""
    generate_ues()


def generate_ues():
    """Loads an osm file and plots it."""

    # Path to OSM file

    dir_this = os.path.abspath(os.path.dirname(__file__))
    dir_src = os.path.abspath(os.path.dirname(dir_this))
    dir_data = os.path.abspath(os.path.join(dir_src, "data"))
    abs_file = os.path.abspath(os.path.join(dir_data, "campus_melaten.osm"))

    # Make output data directory

    workspace = ut.make_workspace(name_workspace=None)
    # For a custom name change None to "Your custom name"

    example_district = ug.UESGraph()

    # To import buildings and streets from OpenStreetMap data in osm_file
    # the from_osm function is used. This function contains four parameters.
    # In path the full path to input osm file is given. Name gives the name of
    # the city for the boundary check. If the parameter check_boundary is true,
    # the city boundary will be extracted from the osm file and only nodes
    # within this boundary will be accepted. The transform_positions parameter
    # decides whether the position data should be transfomed to coordinates
    # using metric system. By default it is set 'true'. If it is set 'false'
    # the positions will remain in longitude and latitude as read from the
    # OSM file.

    example_district.from_osm(
        osm_file=abs_file,
        name="Melaten",
        check_boundary=False,
        transform_positions=True,
    )

    scaling_factor = 10

    # Plot simple osm layout using show_network function

    save_as = os.path.join(workspace, "simplified_melaten_osm.png")
    vis = ug.Visuals(example_district)
    vis.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor, simple=True
    )

    # Analyze the building statistics for the district and distinguish them by
    # area in small, medium and large buildings.

    area_list(example_district)

    # Remove all buildings from the graph that have less area than parameter
    # 'min_area'. This function has two parameters 'input_graph' and 'min_area'.

    remove_small_buildings(example_district, 100)

    # Plot full network layout with street labels to remove them afterwards

    save_as = os.path.join(workspace, "example_melaten_osm.png")
    vis = ug.Visuals(example_district)
    vis.show_network(
        save_as=save_as, labels="street", show_plot=False, scaling_factor=scaling_factor
    )

    # Plot full network layout of building labels to remove them

    save_as = os.path.join(workspace, "example_melaten_osm_bldgs.png")
    vis = ug.Visuals(example_district)
    vis.show_network(
        save_as=save_as,
        labels="building",
        show_plot=False,
        scaling_factor=scaling_factor,
    )

    # now we need to remove some street nodes which are not connected.
    # or connect them by hand
    # 1350 - 1357
    # 2257 - 2271
    # 1135, 1136, 1138, 1448 - 1455
    # 1762 - 1767

    street_nodes_to_remove = [1135, 1136, 1138, 1888, 1889]
    street_nodes_to_remove += list(range(1350, 1358))
    street_nodes_to_remove += list(range(2257, 2272))
    street_nodes_to_remove += list(range(1448, 1456))
    street_nodes_to_remove += list(range(1762, 1768))

    # Remove street nodes

    for node in street_nodes_to_remove:
        if node in example_district.nodelist_street:
            example_district.remove_node(node)
            example_district.nodelist_street.remove(node)

    # now we remove the buildings which should not be included

    example_district.remove_building(1121)

    # Plot full network layout without the unnecessary buildings and streets

    save_as = os.path.join(workspace, "example_melaten_osm_wo_large_bldgs.png")
    vis = ug.Visuals(example_district)
    vis.show_network(
        save_as=save_as, labels="street", show_plot=False, scaling_factor=scaling_factor
    )

    save_as = os.path.join(workspace, "simplified_melaten_osm_wo_large_bldgs.png")
    vis = ug.Visuals(example_district)
    vis.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor, simple=True
    )

    # Now we can start generating an exemplary and randomized district heating
    # network. A heating supply building is added using the
    # add_district_heating_buildings.

    supply_node = add_district_heating_buildings(example_district, "87275925")

    # Generate a urban energy system using the 'UESGenerator' and the data just
    # created from OSM file.

    uesgenerator = uesgen.UESGenerator()
    uesgenerator.uesgraph = example_district

    # Find street crossings

    uesgenerator.find_crossings()

    # Cluster buildings for a more generic usage using the cluster_bldg
    # function. The parameter 'eps' indicates the maximum distance (in m) that
    # points can be away from each other to be considered a cluster.

    uesgenerator = utils.cluster_bldg(uesgenerator, eps=50)

    # Adds the network to the district based on the street layout using
    # add_network_new function. There are three parameters to set. 'supply_node'
    # specifies the heating supply building. 'number_of_buildings' gives
    # the number of buildings to be connected to the heating network and
    # 'success_rate' indicates the probability of a building to be part of the
    # heating network.

    melaten_dhc_example = uesgenerator.add_network_new(
        supply_node=supply_node,
        number_of_buildings=len(example_district.nodelist_building),
        success_rate=1.0,
        workspace=workspace,
    )

    # Generate a heating network as subgraph and remove any edges and network
    # nodes not connected to a supply node of type 'heating'.

    heating_network = melaten_dhc_example.create_subgraphs("heating")["default"]
    heating_network.remove_unconnected_nodes("heating")

    # Plot simple osm layout

    save_as = os.path.join(workspace, "melaten_dhc_network.png")
    vis = ug.Visuals(heating_network)
    vis.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor, simple=True
    )

    # Plot detailed osm layout

    save_as = os.path.join(workspace, "melaten_dhc_network_detail.png")
    vis = ug.Visuals(heating_network)
    vis.show_network(save_as=save_as, show_plot=False, scaling_factor=scaling_factor)

    # Print out the length of all edges for the heating network in meter.

    print(heating_network.calc_network_length("heating"))

    return example_district


def remove_small_buildings(input_graph, min_area):
    """
    Remove all buildings from the graph that have area less than `min_area´.

    Parameters
    ----------
    input_graph : uesgraphs.uesgraph.UESGraph object
        An UESGraph that will be analysed for data
    min_area : float
        Minimum area for a building to remain in the graph

    Returns
    -------
    input_graph : uesgraphs.uesgraph.UESGraph object
        An UESGraph that will be analysed for data
    """
    to_remove = []
    for building in input_graph.nodelist_building:
        if "area" in input_graph.node[building]:
            if input_graph.node[building]["area"] <= min_area:
                to_remove.append(building)

    for building in to_remove:
        input_graph.remove_building(building)


def add_district_heating_buildings(input_graph, supply_id_osm):
    """
    Set the given osm id as supply and remaining buildings as demand.

    Parameters
    ----------
    input_graph : uesgraphs.uesgraph.UESGraph object
        An UESGraph that will be analysed for data
    supply_id_osm:
        The osm id of the building which is used as the supply node

    Returns
    -------
    None
    """
    for node in input_graph.nodelist_building:
        if input_graph.nodes[node]["osm_id"] == supply_id_osm:
            input_graph.nodes[node]["is_supply_heating"] = True
            supply_node = node
    return supply_node


def area_list(input_graph):
    """
    List the average area of small, medium and large buildings

    Small: < 200 m²
    Medium: 200 m² < 1000 m²
    Large: > 1000 m²

    Parameters
    ----------
    input_graph : uesgraphs.uesgraph.UESGraph object
        An UESGraph that will be analysed for data
    """
    area_list_small = []
    area_list_medium = []
    area_list_large = []
    list_small_buildings = []
    list_medium_buildings = []
    list_large_buildings = []
    for building in input_graph.nodelist_building:
        if "area" in input_graph.node[building]:

            if input_graph.node[building]["area"] <= 200:
                list_small_buildings.append(input_graph.node[building])
                area_list_small.append(input_graph.node[building]["area"])

            if (
                input_graph.node[building]["area"] > 200
                and input_graph.node[building]["area"] <= 1000
            ):
                list_medium_buildings.append(input_graph.node[building])
                area_list_medium.append(input_graph.node[building]["area"])

            if input_graph.node[building]["area"] > 1000:
                list_large_buildings.append(input_graph.node[building])
                area_list_large.append(input_graph.node[building]["area"])

    # small buildings
    l_small = len(list_small_buildings)
    print("Small buildings:", l_small)
    a_small_sum = sum(area_list_small)
    a_small_mid = a_small_sum / l_small
    print("Small buildings: Avarage area =", a_small_mid)

    # medium buildings
    l_medium = len(list_medium_buildings)
    print("Medium buildings:", l_medium)
    a_medium_sum = sum(area_list_medium)
    a_medium_mid = a_medium_sum / l_medium
    print("Medium buildings: Avarage area =", a_medium_mid)

    # large buildings
    l_large = len(list_large_buildings)
    print("Large buildings:", l_large)
    a_large_sum = sum(area_list_large)
    a_large_mid = a_large_sum / l_large
    print("Large buildings: Avarage area =", a_large_mid)

    return input_graph


# Main function
if __name__ == "__main__":
    print("*** Loading osm data ***")
    main()
    print("*** Done ***")
