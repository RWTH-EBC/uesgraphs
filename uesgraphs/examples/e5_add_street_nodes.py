"""This module includes tests and demonstrations of uesgraphs"""

import os
from shapely.geometry import Point
import uesgraphs as ug

import matplotlib.pyplot as plt


def main():

    street_nodes()


def street_nodes():
    """Tests the street nodes implementation
    """
    workspace = make_workspace('demo')

    a = Point(1.234567892345678923456789, 1)
    b = Point(1.234567892345678923456788, 1)
    assert a == b

    this_district = ug.UESGraph()
    sn_11 = this_district.add_street_node(position=Point(1, 1))
    sn_12 = this_district.add_street_node(position=Point(1, 2))
    sn_13 = this_district.add_street_node(position=Point(2, 2))
    sn_14 = this_district.add_street_node(position=Point(2, 1))

    this_district.add_edge(sn_11, sn_12)
    this_district.add_edge(sn_12, sn_13)
    this_district.add_edge(sn_13, sn_14)
    this_district.add_edge(sn_14, sn_11)

    for street_node in this_district.nodelist_street:
        print('Street node:', street_node, this_district.node[street_node])

    save_as = os.path.join(workspace, '09_Streets.png')
    vis_streets = ug.Visuals(this_district)
    vis_streets.show_network(save_as=save_as, show_plot=False)


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
    print("**** Creating graph with street nodes ***")
    main()
    print("*** Done ***")
