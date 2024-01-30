# -*- coding: utf-8 -*-
# @Author: MichaMans
# @Date:   2019-03-12 08:26:20
# @Last Modified by:   Frye789
# @Last Modified time: 2019-07-11 15:06:00


import os
from shapely.geometry import Point
import uesgraphs as ug
import uesgraphs.utilities as ut


def main():
    """Main function."""
    load_json()
    load_osm()
    graph = ug.UESGraph()
    graph.to_json()


def load_json():
    """Loads a nodes.json and plots it."""

    # Path to JSON file.

    dir_this = os.path.abspath(os.path.dirname(__file__))
    dir_src = os.path.abspath(os.path.dirname(dir_this))
    dir_data = os.path.abspath(os.path.join(dir_src, "data"))
    abs_file = os.path.abspath(os.path.join(dir_data, "only_heating.json"))

    example_district = ug.UESGraph()

    # To import the network data from a JSON file the from_json function is
    # used. This function contains three parameters. In path the information
    # where to find input file is given. network_type specifies the type of
    # the destination network as {'heating', 'cooling', 'electricity', 'gas',
    # 'others'}. The third parameter check_overlap is 'false' by default. To
    # check if network node positions overlap existing network nodes set it
    # 'true'. Below a JSON file is imported from 'abs_file' as a heating
    # network.

    example_district.from_json(path=abs_file, network_type="heating")

    workspace = ut.make_workspace(name_workspace=None)
    # For a custom name change None to "Your custom name"

    scaling_factor = 10

    # Plot full network layout

    save_as = os.path.join(workspace, "example_district.png")
    vis = ug.Visuals(example_district)
    vis.show_network(save_as=save_as, show_plot=False, scaling_factor=scaling_factor)

    print(example_district.calc_network_length("heating"))

    # Plot simple network layout

    save_as = os.path.join(workspace, "simplified_district.png")
    vis = ug.Visuals(example_district)
    vis.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor, simple=True
    )

    return example_district


def load_osm():
    """Loads an osm file and plots it."""

    # Path to OSM file.

    dir_this = os.path.abspath(os.path.dirname(__file__))
    dir_src = os.path.abspath(os.path.dirname(dir_this))
    dir_data = os.path.abspath(os.path.join(dir_src, "data"))
    abs_file = os.path.abspath(os.path.join(dir_data, "campus_melaten.osm"))

    workspace = ut.make_workspace()

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

    example_district.from_osm(osm_file=abs_file, name="Melaten", check_boundary=False)

    return example_district


# Main function
if __name__ == "__main__":
    print("*** Loading dhc graph ***")
    main()
    print("*** Done ***")
