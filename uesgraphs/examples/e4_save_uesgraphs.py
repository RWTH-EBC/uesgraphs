"""This module includes tests and demonstrations of uesgraphs"""

import os
from shapely.geometry import Point
import uesgraphs as ug

import matplotlib.pyplot as plt


def main():

    to_json()


def simple_dhc_model():
    """Initializes an UESGraph object, adds 2 heating and cooling networks each

    Returns
    -------
    example_district : uesgraphs.uesgraph.UESGraph object
        An UESGraph containing 4 buildings connected to 2 heating supplies and
        2 cooling supplies via 2 heating and cooling networks each
    """
    example_district = ug.UESGraph()
    supply_heating_1 = example_district.add_building(position=Point(1, 2),
                                                     is_supply_heating=True)
    supply_cooling_1 = example_district.add_building(position=Point(1, 1),
                                                     is_supply_cooling=True)

    building_1 = example_district.add_building(name='building_1',
                                               position=Point(2, 3))
    building_2 = example_district.add_building(name='building_2',
                                               position=Point(3, 3))
    building_3 = example_district.add_building(name='building_3',
                                               position=Point(4, 3))
    building_4 = example_district.add_building(name='building_4',
                                               position=Point(5, 3))

    hn_1 = example_district.add_network_node(network_type='heating',
                                             position=Point(2, 2))
    hn_2 = example_district.add_network_node(network_type='heating',
                                             position=Point(3, 2))
    example_district.add_edge(supply_heating_1, hn_1)
    example_district.add_edge(hn_1, building_1)
    example_district.add_edge(hn_1, hn_2)
    example_district.add_edge(hn_2, building_2)

    cn_1 = example_district.add_network_node(network_type='cooling',
                                             position=Point(3, 1))
    example_district.add_edge(supply_cooling_1, cn_1)
    example_district.add_edge(cn_1, building_2)

    example_district.add_network('heating', 'heating_2')
    example_district.add_network('cooling', 'cooling_2')
    supply_heating_2 = example_district.add_building(position=Point(1, 4),
                                                     is_supply_heating=True)
    supply_cooling_2 = example_district.add_building(position=Point(1, 5),
                                                     is_supply_cooling=True)
    hn_3 = example_district.add_network_node(network_type='heating',
                                             position=Point(4, 4),
                                             network_id='heating_2')
    example_district.add_edge(supply_heating_2, hn_3)
    example_district.add_edge(hn_3, building_3)

    cn_2 = example_district.add_network_node(network_type='cooling',
                                             position=Point(2, 5),
                                             network_id='cooling_2')
    example_district.add_edge(supply_cooling_2, cn_2)
    example_district.add_edge(cn_2, building_1)
    cn_3 = example_district.add_network_node(network_type='cooling',
                                             position=Point(5, 5),
                                             network_id='cooling_2')
    example_district.add_edge(cn_2, cn_3)
    example_district.add_edge(cn_3, building_4)

    return example_district


def to_json():
    """Demos the output of an uesgraph to JSON
    """
    workspace = make_workspace('json_output')

    example_district = simple_dhc_model()
    example_district.to_json(path=workspace,
                             name='demo')


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
    print("*** Saving uesgraphs to json ***")
    main()
    print("*** Done ***")
