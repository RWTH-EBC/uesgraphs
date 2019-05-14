"""This module includes tests and demonstrations of uesgraphs"""

import os
from shapely.geometry import Point
import uesgraphs as ug

import matplotlib.pyplot as plt


def main():

    additional_attrib()


def additional_attrib():
    """Demonstration for adding additional attributes to building nodes

    This approach can be used to enhance the functionality of an uesgraph
    with additional attributes, e.g. assigning a building object to a
    building node
    """

    this_district = ug.UESGraph()

    building_1 = this_district.add_building(position=Point(2, 3))
    this_district.nodes[building_1]['building'] = 'building_object_goes_here'

    print(this_district.nodes(data=True))


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
    print("*** Adding additional attributes to building in graph ***")
    main()
    print("*** Done ***")
