"""This module includes tests and demonstrations of uesgraphs"""

import os
from shapely.geometry import Point
import uesgraphs as ug
import uesgraphs.utilities as ut
import matplotlib.pyplot as plt

from uesgraphs.examples import e2_simple_dhc as e2


def main():

    # In e2_simple_dhc a simple district heating cooling network is created to
    # get this network the example is rerunned.

    example_district = e2.simple_dhc_model()

    # To add more buildings and network nodes the add_more_networks function is
    # used.

    example_district = add_more_networks(example_district)


def add_more_networks(example_district):
    """Adds an electric grid to the simple_dhc_model example

    Parameters
    ----------
    example_district : uesgraphs.uesgraph.UESGraph object
        An UESGraph containing 4 buildings connected to 2 heating supplies and
        2 cooling supplies via 2 heating and cooling networks each from
        `simple_dhc_model()`

    Returns
    -------
    example_district : uesgraphs.uesgraph.UESGraph object
        An UESGraph containing 8 buildings and various supplies and networks
        to illustrate UESGraph use
    """

    # Node numbers of the buildings are retrieved and saved.

    building_1 = example_district.nodes_by_name["building_1"]
    building_2 = example_district.nodes_by_name["building_2"]
    building_3 = example_district.nodes_by_name["building_3"]
    building_4 = example_district.nodes_by_name["building_4"]

    # Add electricity network
    # To generate a electricity supply building the
    # example_district.add_building function is used. Nine
    # parameters are available. The name and the position of the building node
    # need to be set. If the building should be a supply station this can be
    # set by one of the following parameters: is_supply_heating,
    # is_supply_cooling, is_supply_electricity, is_supply_gas and
    # is_supply_other. Below a electricity supply building node called
    # `supply_electricity` is added.

    supply_electricity = example_district.add_building(
        position=Point(6, 2), is_supply_electricity=True
    )

    # To generate a network node the function example_district.add_network_node
    # is used. A network node should not be placed at positions where there
    # is already a node of the same network or a building node. Eight
    # parameters are available. network_type defines the network into which
    # to add the node.The position is compulsory. Below four network nodes for
    # a electricity network are added.

    en_1 = example_district.add_network_node(
        network_type="electricity", position=Point(5, 2.5)
    )
    en_2 = example_district.add_network_node(
        network_type="electricity", position=Point(4, 2.5)
    )
    en_3 = example_district.add_network_node(
        network_type="electricity", position=Point(3, 2.5)
    )
    en_4 = example_district.add_network_node(
        network_type="electricity", position=Point(2, 2.5)
    )

    # The nodes of the electricity network are connected using the
    # example_district.add_edge function.

    example_district.add_edge(en_1, building_4)
    example_district.add_edge(en_2, building_3)
    example_district.add_edge(en_3, building_2)
    example_district.add_edge(en_4, building_1)
    example_district.add_edge(en_1, en_2)
    example_district.add_edge(en_2, en_3)
    example_district.add_edge(en_3, en_4)
    example_district.add_edge(en_1, supply_electricity)

    # Add more buildings supplied by gas and electricity

    building_5 = example_district.add_building(position=Point(7, 3))
    building_6 = example_district.add_building(position=Point(7, 4))
    building_7 = example_district.add_building(position=Point(7, 5))

    # Add three network nodes of the type electricity.

    en_5 = example_district.add_network_node(
        network_type="electricity", position=Point(6.5, 3)
    )
    en_6 = example_district.add_network_node(
        network_type="electricity", position=Point(6.5, 4)
    )
    en_7 = example_district.add_network_node(
        network_type="electricity", position=Point(6.5, 5)
    )

    # Using example_district.add_edge the nodes of electricity network are
    # connected.

    example_district.add_edge(en_5, en_6)
    example_district.add_edge(en_6, en_7)
    example_district.add_edge(en_5, supply_electricity)
    example_district.add_edge(en_5, building_5)
    example_district.add_edge(en_6, building_6)
    example_district.add_edge(en_7, building_7)

    # Add a network of type 'gas'.
    # Add a new supply building for gas called `supply_gas`.

    supply_gas = example_district.add_building(
        position=Point(8, 1), is_supply_gas=True
    )

    # Add network nodes for gas network.

    gn_1 = example_district.add_network_node(
        network_type="gas", position=Point(8, 3)
    )
    gn_2 = example_district.add_network_node(
        network_type="gas", position=Point(8, 4)
    )
    gn_3 = example_district.add_network_node(
        network_type="gas", position=Point(8, 5)
    )

    # Connect nodes of gas network.

    example_district.add_edge(gn_1, gn_2)
    example_district.add_edge(gn_2, gn_3)
    example_district.add_edge(gn_1, supply_gas)
    example_district.add_edge(gn_1, building_5)
    example_district.add_edge(gn_2, building_6)
    example_district.add_edge(gn_3, building_7)

    # Add a network of type 'other'
    # Generate a supply building of type 'other'.

    supply_other = example_district.add_building(
        position=Point(7.5, 7), is_supply_other=True
    )

    # Generate two network nodes of type 'other' using the add_network_node
    # function.

    on_1 = example_district.add_network_node(
        network_type="others", position=Point(7.5, 5)
    )
    on_2 = example_district.add_network_node(
        network_type="others", position=Point(7.5, 4)
    )

    # Connect the nodes of network 'other'.

    example_district.add_edge(on_1, on_2)
    example_district.add_edge(on_1, supply_other)
    example_district.add_edge(on_1, building_7)
    example_district.add_edge(on_2, building_6)

    # Add street nodes using the example_district.add_street_node function.
    # In this function five parameters are available. The position of the
    # street can be set. Also the resolution can be given which means the
    # minimum distance between two points. The check_overlap parameter is set
    # true by default. Below four streets are generated in block 1 and four
    # street are generated in block 2.

    sn_11 = example_district.add_street_node(position=Point(1, 2.5), block=1)
    sn_12 = example_district.add_street_node(position=Point(6, 2.5), block=1)
    sn_13 = example_district.add_street_node(position=Point(6, 3.5), block=1)
    sn_14 = example_district.add_street_node(position=Point(1, 3.5), block=1)

    sn_21 = example_district.add_street_node(position=Point(6, 5.5), block=2)
    sn_22 = example_district.add_street_node(position=Point(6, 2.5), block=2)
    sn_23 = example_district.add_street_node(position=Point(8, 2.5), block=2)
    sn_24 = example_district.add_street_node(position=Point(8, 5.5), block=2)

    # Connecting streets of block 1

    example_district.add_edge(sn_11, sn_12)
    example_district.add_edge(sn_12, sn_13)
    example_district.add_edge(sn_13, sn_14)
    example_district.add_edge(sn_14, sn_11)

    # Connecting street of block 2

    example_district.add_edge(sn_21, sn_22)
    example_district.add_edge(sn_22, sn_23)
    example_district.add_edge(sn_23, sn_24)
    example_district.add_edge(sn_24, sn_21)

    return example_district


# Main function
if __name__ == "__main__":
    print("*** Generating simple dhc model ***")
    print("*** Adding more graphs ***")
    main()
    print("*** Done ***")
