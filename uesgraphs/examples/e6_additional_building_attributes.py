"""Demonstration for adding additional attributes to building nodes (only terminal output)"""

import os
from shapely.geometry import Point
import uesgraphs as ug



def main():

    additional_attrib()


def additional_attrib():
    """Demonstration for adding additional attributes to building nodes

    This approach can be used to enhance the functionality of an uesgraph
    with additional attributes, e.g. assigning a building object to a
    building node
    
    Additional advise: Nodes and edges of an uesgraph can be treated similar.
    Important is to understand the given dictionary structure and the idea
    of also adding additional attributes to edges/nodes/buildings
    """

    this_district = ug.UESGraph()

    # A building node is added using the add_building function.

    building_1 = this_district.add_building(position=Point(2, 3))

    # An additional attribute is added to building_1.

    this_district.nodes[building_1]["building"] = "building_object_goes_here"

    # The attributes of building_1 are printed.

    print(this_district.nodes(data=True))


# Main function
if __name__ == "__main__":
    print("*** Adding additional attributes to building in graph ***")
    main()
    print("*** Done ***")
