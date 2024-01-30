"""This module includes tests and demonstrations of uesgraphs"""

import os
from shapely.geometry import Point
import uesgraphs as ug
import uesgraphs.utilities as ut
import matplotlib.pyplot as plt


def main():

    street_nodes()


def street_nodes():
    """Tests the street nodes implementation
    """

    # Generate a workspace path.

    workspace = ut.make_workspace("demo")  # C:/User/UESgraphOutput

    # Create two points

    a = Point(1.234567892345678923456789, 1)
    b = Point(1.234567892345678923456788, 1)
    assert a == b

    # A district network is generated

    this_district = ug.UESGraph()

    # Add street nodes using the this_district.add_street_node function.
    # In this function five parameters are available. The position of the
    # street can be set. Also the resolution can be given which means the
    # minimum distance between two points. The check_overlap parameter is set
    # true by default. Below four streets are generated.

    sn_11 = this_district.add_street_node(position=Point(1, 1))
    sn_12 = this_district.add_street_node(position=Point(1, 2))
    sn_13 = this_district.add_street_node(position=Point(2, 2))
    sn_14 = this_district.add_street_node(position=Point(2, 1))

    # The street nodes are connected to each other.

    this_district.add_edge(sn_11, sn_12)
    this_district.add_edge(sn_12, sn_13)
    this_district.add_edge(sn_13, sn_14)
    this_district.add_edge(sn_14, sn_11)

    # Printout street node names.

    for street_node in this_district.nodelist_street:
        print("Street node:", street_node, this_district.node[street_node])

    # Storage path for visuals of streets.

    save_as = os.path.join(workspace, "09_Streets.png")

    # To visualize the district network ug.Visuals is used. The visualization
    # output will be following the graph layout specified in the input uesgraph.

    vis_streets = ug.Visuals(this_district)

    # Saving the visualization to the storage path.

    vis_streets.show_network(save_as=save_as, show_plot=False)


# Main function
if __name__ == "__main__":
    print("**** Creating graph with street nodes ***")
    main()
    print("*** Done ***")
