"""This module includes tests and demonstrations of uesgraphs"""

import os
from shapely.geometry import Point
import uesgraphs as ug
import matplotlib.pyplot as plt


def main():

    example_readme()


def example_readme():
    """The example given in the README.md file
    """

    workspace = make_workspace("readme")

    graph = ug.UESGraph()

    # To generate a building the function graph.add_building is used. Nine
    # parameters are available. The name and the position of the building node
    # need to be set. If the building should be a supply station this can be
    # set by one of the following parameters: is_supply_heating,
    # is_supply_cooling, is_supply_electricity, is_supply_gas and
    # is_supply_other. Below a heat supply building node called `Supply`
    # and a demand building node called `Building 1` are added.

    supply = graph.add_building(
        name="Supply",
        position=Point(0, 10),
        is_supply_heating=True)

    demand = graph.add_building(
        name="Building 1",
        position=Point(50, 15))

    # To generate a network node the function graph.add_network_node is used.
    # A network node should not be placed at positions where there is already
    # a node of the same network or a building node. Eight parameters are
    # available. network_type defines the network into which to add the node.
    # The position is compulsory. Below a network node for a heating network is
    # added.

    heating_node = graph.add_network_node(
        network_type="heating",
        position=Point(30, 5))

    # To connect the different nodes graph.add_edge is used. Below the supply
    # is connected to the heating node and the heating node to the demand.

    graph.add_edge(supply, heating_node)
    graph.add_edge(heating_node, demand)

    save_as = os.path.join(workspace, "graph.png")

    # The energy system can be plotted using the following function.

    vis = ug.Visuals(graph)
    vis.show_network(save_as=save_as, scaling_factor=30)


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
    workspace = os.path.join(ues_dir, "workspace")
    if not os.path.exists(workspace):
        os.mkdir(workspace)

    if name_workspace is not None:
        workspace = os.path.join(workspace, name_workspace)
        if not os.path.exists(workspace):
            os.mkdir(workspace)

    return workspace


# Main function
if __name__ == "__main__":
    print("*** Generating example readme ***")
    main()
    print("*** Done ***")
