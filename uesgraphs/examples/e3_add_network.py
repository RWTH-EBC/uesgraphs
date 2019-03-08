"""This module includes tests and demonstrations of uesgraphs"""

import os
from shapely.geometry import Point
import uesgraphs as ug

import matplotlib.pyplot as plt

from uesgraphs.examples import e2_simple_dhc as e2


def main():

    example_district = e2.simple_dhc_model()
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
    building_1 = example_district.nodes_by_name['building_1']
    building_2 = example_district.nodes_by_name['building_2']
    building_3 = example_district.nodes_by_name['building_3']
    building_4 = example_district.nodes_by_name['building_4']

    # Add electricity network
    supply_electricity = example_district.add_building(
        position=Point(6, 2),
        is_supply_electricity=True,
    )
    en_1 = example_district.add_network_node(network_type='electricity',
                                             position=Point(5, 2.5))
    en_2 = example_district.add_network_node(network_type='electricity',
                                             position=Point(4, 2.5))
    en_3 = example_district.add_network_node(network_type='electricity',
                                             position=Point(3, 2.5))
    en_4 = example_district.add_network_node(network_type='electricity',
                                             position=Point(2, 2.5))
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
    en_5 = example_district.add_network_node(network_type='electricity',
                                             position=Point(6.5, 3))
    en_6 = example_district.add_network_node(network_type='electricity',
                                             position=Point(6.5, 4))
    en_7 = example_district.add_network_node(network_type='electricity',
                                             position=Point(6.5, 5))
    example_district.add_edge(en_5, en_6)
    example_district.add_edge(en_6, en_7)
    example_district.add_edge(en_5, supply_electricity)
    example_district.add_edge(en_5, building_5)
    example_district.add_edge(en_6, building_6)
    example_district.add_edge(en_7, building_7)

    supply_gas = example_district.add_building(position=Point(8, 1),
                                               is_supply_gas=True)
    gn_1 = example_district.add_network_node(network_type='gas',
                                             position=Point(8, 3))
    gn_2 = example_district.add_network_node(network_type='gas',
                                             position=Point(8, 4))
    gn_3 = example_district.add_network_node(network_type='gas',
                                             position=Point(8, 5))
    example_district.add_edge(gn_1, gn_2)
    example_district.add_edge(gn_2, gn_3)
    example_district.add_edge(gn_1, supply_gas)
    example_district.add_edge(gn_1, building_5)
    example_district.add_edge(gn_2, building_6)
    example_district.add_edge(gn_3, building_7)

    # Add a network of type 'other'
    supply_other = example_district.add_building(position=Point(7.5, 7),
                                                 is_supply_other=True)
    on_1 = example_district.add_network_node(network_type='others',
                                             position=Point(7.5, 5))
    on_2 = example_district.add_network_node(network_type='others',
                                             position=Point(7.5, 4))
    example_district.add_edge(on_1, on_2)
    example_district.add_edge(on_1, supply_other)
    example_district.add_edge(on_1, building_7)
    example_district.add_edge(on_2, building_6)

    # Add street nodes
    sn_11 = example_district.add_street_node(position=Point(1, 2.5), block=1)
    sn_12 = example_district.add_street_node(position=Point(6, 2.5), block=1)
    sn_13 = example_district.add_street_node(position=Point(6, 3.5), block=1)
    sn_14 = example_district.add_street_node(position=Point(1, 3.5), block=1)

    sn_21 = example_district.add_street_node(position=Point(6, 5.5), block=2)
    sn_22 = example_district.add_street_node(position=Point(6, 2.5), block=2)
    sn_23 = example_district.add_street_node(position=Point(8, 2.5), block=2)
    sn_24 = example_district.add_street_node(position=Point(8, 5.5), block=2)

    example_district.add_edge(sn_11, sn_12)
    example_district.add_edge(sn_12, sn_13)
    example_district.add_edge(sn_13, sn_14)
    example_district.add_edge(sn_14, sn_11)

    example_district.add_edge(sn_21, sn_22)
    example_district.add_edge(sn_22, sn_23)
    example_district.add_edge(sn_23, sn_24)
    example_district.add_edge(sn_24, sn_21)

    return example_district


def make_workspace(name_workspace=None):
    """Creates a local workspace with given name

    If no name is given, the general workspace directory will be used

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
    workspace = os.path.join(ues_dir, 'workspace')
    if not os.path.exists(workspace):
        os.mkdir(workspace)

    if name_workspace is not None:
        workspace = os.path.join(workspace, name_workspace)
        if not os.path.exists(workspace):
            os.mkdir(workspace)

    return workspace


# Main function
if __name__ == '__main__':
    print("*** Generating simple dhc model ***")
    print("*** Adding more graphs ***")
    main()
    print("*** Done ***")
