"""This module includes tests and demonstrations of uesgraphs"""

import os
import random
import uesgraphs.utilities as ut
from shapely.geometry import Point
import uesgraphs as ug
import matplotlib.pyplot as plt

from uesgraphs.examples import e2_simple_dhc as e2
from uesgraphs.examples import e3_add_network as e3


def main():

    plot_example_networks()


def plot_example_networks():
    """Plots example networks to demo uesgraphs
    """

    # The function of example e2 is used to generate an example district.

    example_district = e2.simple_dhc_model()

    # The add_more_networks function of example e3 generates more network nodes.

    example_district = e3.add_more_networks(example_district)

    # Workspace directory is set using the make_workspace function.

    workspace = ut.make_workspace("demo")

    # The scaling_factor for the following plots is set.

    scaling_factor = 10

    # Plot full network layout
    # Directory where to save the plot is set.
    # The Visuals function is applied to example_district.
    # The example_district is plotted using the show_network function. In this
    # function 15 parameters are available. Below the hole network layout is
    # plotted.

    save_as = os.path.join(workspace, "01_district.png")
    vis = ug.Visuals(example_district)
    vis.show_network(save_as=save_as, show_plot=False, scaling_factor=scaling_factor)

    # Plot heating network
    # Directory where to save the plot is set.
    # A sub network is created using the create_subgraphs function.
    # The Visuals function is applied to the heating sub network.
    # The heating sub network is plotted using the show_network function. In this
    # function 15 parameters are available.

    save_as = os.path.join(workspace, "02_heating_1.png")
    heating_network = example_district.create_subgraphs("heating")["default"]
    vis_heating = ug.Visuals(heating_network)
    vis_heating.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor
    )

    # Plot cooling network
    # Create directory where to save the plot.
    # A sub network of the cooling network is created using the create_subgraphs
    # function. The Visuals function is applied to the cooling sub network.
    # The cooling sub network is plotted using the show_network function. In
    # this function 15 parameter are available.

    save_as = os.path.join(workspace, "03_cooling_1.png")
    cooling_network = example_district.create_subgraphs("cooling")["default"]
    vis_cooling = ug.Visuals(cooling_network)
    vis_cooling.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor
    )

    # Plot heating 2 network
    # A second heating sub network is created and plotted.

    save_as = os.path.join(workspace, "04_heating_2.png")
    heating_network_2 = example_district.create_subgraphs("heating")["heating_2"]
    vis_heating_2 = ug.Visuals(heating_network_2)
    vis_heating_2.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor
    )

    # Plot cooling 2 network
    # A second cooling sub network is created and plotted.

    save_as = os.path.join(workspace, "05_cooling_2.png")
    cooling_network_2 = example_district.create_subgraphs("cooling")["cooling_2"]
    vis_cooling_2 = ug.Visuals(cooling_network_2)
    vis_cooling_2.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor
    )

    # Plot electricity network
    # An electricity sub network is created using the create_subgraphs function.
    # Afterwards it is plotted using the show_network function.

    save_as = os.path.join(workspace, "06_electricity.png")
    electricity_network = example_district.create_subgraphs("electricity")["default"]
    vis_electricity = ug.Visuals(electricity_network)
    vis_electricity.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor
    )

    # Plot gas network
    # A gas sub network is created using the create_subgraphs function.
    # Afterwards it is plotted using the show_network function.

    save_as = os.path.join(workspace, "07_gas.png")
    gas_network = example_district.create_subgraphs("gas")["default"]
    vis_gas = ug.Visuals(gas_network)
    vis_gas.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor
    )

    # Plot other networks
    # A sub network called 'other' is created using the create_subgraphs
    # function. Afterwards it is plotted using the show_network function.

    save_as = os.path.join(workspace, "08_others.png")
    others_network = example_district.create_subgraphs("others")["default"]
    vis_others = ug.Visuals(others_network)
    vis_others.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor
    )

    # Plot network in 3d layout
    # To generate a 3D view of the network the function network_explosion is
    # used. Six parameters can be adjusted in this function. For generating
    # a 3D view without the explosion into different layers the networks
    # parameter is an empty list. In case of network explosion the networks
    # parameter is set ['all']. Instead of ['all'], the networks list can
    # specify which networks should be plotted. Accepted items are
    # {'heating', 'cooling', 'electricity', 'gas', 'others'}. If the networks
    # list is not specified it is set to ['all'].

    save_as = os.path.join(workspace, "09_network_3d.png")
    vis = ug.Visuals(example_district)
    vis.network_explosion(
        save_as=save_as,
        show_plot=False,
        angle=250,
        scaling_factor=scaling_factor * 5,
        networks=[],
    )

    # Plot network explosion
    # To generate a 3D view with network explosion the function
    # network_explosion is used. Six parameters can be adjusted in this
    # function. For generating a 3D view with the explosion into different
    # layers the networks parameter is set ['all']. Instead of ['all'], the
    # networks list can specify which networks should be plotted. Accepted
    # items are {'heating', 'cooling', 'electricity', 'gas', 'others'}. If the
    # networks list is not specified it is set to ['all']. Below the networks
    # parameter is left out thus it is set to ['all'].

    save_as = os.path.join(workspace, "10_network_explosion.png")
    vis = ug.Visuals(example_district)
    vis.network_explosion(
        save_as=save_as,
        show_plot=False,
        angle=250,
        scaling_factor=scaling_factor * 5
    )

    # Plot simple network visualization
    # For very large uesgraphs, the standard plotting may take too long
    # (hours...). In these cases, the show_network function can be adjusted
    # by `simple=True`. This gives faster results.

    save_as = os.path.join(workspace, "11_simple.png")
    scaling_factor = 50
    vis = ug.Visuals(example_district)
    fig = vis.show_network(
        save_as=save_as, show_plot=False, scaling_factor=scaling_factor, simple=True
    )

    # Plot diameters for two edges
    # To show the relative diameter of the pipe set show_diameters = True.

    save_as = os.path.join(workspace, "12_diameters.png")
    random.seed(12345)

    # Create a subgraph containing just the heating network.

    heating_network_1 = example_district.create_subgraphs(
        network_type="heating", all_buildings=False
    )["default"]

    # Create a list with edges of the network and sorts the entries in
    # ascending order.

    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)

    # Put some random diameters to the edge data.

    for edge in edgelist_sorted:
        diameter = random.uniform(0.05, 0.5)
        print("diameter", diameter)
        heating_network_1.edges[edge[0], edge[1]]["diameter"] = diameter
    print(heating_network_1.edges(data=True))

    # The network is plotted using the show_diameters parameter.

    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        show_diameters=True,
    )

    # Plot diameters scaling
    # As in the example before the relative diameter of the pipe is shown
    # using show_diameters. Additional a scaling_factor_diameter is used to
    # scale the width of lines.

    save_as = os.path.join(workspace, "13_diameters_scaling.png")
    random.seed(12345)

    # A subgraph is created containing the heating network.

    heating_network_1 = example_district.create_subgraphs(
        network_type="heating", all_buildings=False
    )["default"]

    # Creates a list with edges of the network and sorts the entries in
    # ascending order.

    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)

    # Put some random diameters to the edge data.

    for edge in edgelist_sorted:
        diameter = random.uniform(0.05, 0.5)
        print("diameter", diameter)
        heating_network_1.edges[edge[0], edge[1]]["diameter"] = diameter
    print(heating_network_1.edges(data=True))

    # The subgraph is plotted using the show_diameters parameter and a
    # scaling_factor_diameter of '50'.

    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        scaling_factor_diameter=50,
        show_diameters=True,
    )

    # Plot mass flows
    # Plots edge width according to flow rates in the networks

    save_as = os.path.join(workspace, "14_mass_flows.png")
    random.seed(12345)

    # A subgraph is created containing the heating network.

    heating_network_1 = example_district.create_subgraphs(
        network_type="heating", all_buildings=False
    )["default"]

    # Creates a list with edges of the network and sorts the entries in
    # ascending order.

    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)

    # Put some random mass flow rates to the edge data.

    for edge in edgelist_sorted:
        flow = random.uniform(0.1, 1)
        heating_network_1.edges[edge[0], edge[1]]["mass_flow"] = flow

    # The subgraph 'heating' is plotted using the show_network function.
    # The show_mass_flows parameter is set 'True' thus the pipe width is set
    # according to the mass flow rate.

    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        show_mass_flows=True,
    )

    # Plot temperatures
    # Plots edge temperatures on top of plot

    save_as = os.path.join(workspace, "15_temperatures.png")
    random.seed(12345)

    # A subgraph is created containing the heating network.

    heating_network_1 = example_district.create_subgraphs(
        network_type="heating", all_buildings=False
    )["default"]

    # Creates a list with edges of the network and sorts the entries in
    # ascending order.

    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)

    # Put some random mass flow rates to the edge data.

    for edge in edgelist_sorted:
        flow = random.uniform(0.1, 1)
        heating_network_1.edges[edge[0], edge[1]]["mass_flow"] = flow

    # Creates a list of nodes of the heating network and sorts the entries in
    # ascending order.

    nodelist = list(heating_network_1.nodes())
    nodelist_sorted = sorted(nodelist)

    # Put some random temperatures to the node data.

    for node in nodelist_sorted:
        temp = random.uniform(50, 100)
        heating_network_1.nodes[node]["temperature_supply"] = temp

    # Below the parameters add_edge_temperatures and add_edge_flows are used
    # to plot the temperature to the network.

    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        add_edge_temperatures=True,
        add_edge_flows=True,
        label_size=30,
    )

    # Plot markers
    # Markers are highlighting certain nodes and edges.

    save_as = os.path.join(workspace, "16_markers.png")

    # A subgraph is created containing the heating network.

    heating_network_1 = example_district.create_subgraphs(
        network_type="heating", all_buildings=False
    )["default"]

    # Creates a list with edges of the network and sorts the entries in
    # ascending order.

    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)

    # The first edge in the list is picked to be highlighted.

    for edge in edgelist_sorted:
        edge_to_mark = [edge[0], edge[1]]
        break

    # Creates a list of nodes of the heating network and sorts the entries in
    # ascending order.

    nodelist = list(heating_network_1.nodes())
    nodelist_sorted = sorted(nodelist)

    # The second node in the list is picked to be highlighted.

    node_to_mark = nodelist_sorted[2]

    # Below the parameters node_markers and edge_markers contain lists of nodes
    # and edges which should be marked in the plot.

    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        node_markers=[node_to_mark],
        edge_markers=[edge_to_mark],
        labels="name",
        label_size=25,
    )

    # Plot real 3d
    # Shows an explosion plot of stacked networks in 3d view using
    # show_3d function. There are five parameter available.

    save_as = os.path.join(workspace, "17_3D.png")
    random.seed(12345)

    # A subgraph is created containing the heating network.

    heating_network_1 = example_district.create_subgraphs(
        network_type="heating", all_buildings=False
    )["default"]

    # Creates a list of nodes of the heating network and sorts the entries in
    # ascending order.

    nodelist = list(heating_network_1.nodes())
    nodelist_sorted = sorted(nodelist)

    # Put some random pressure values to the node data.

    for node in nodelist_sorted:
        pressure = random.uniform(2e5, 3e5)
        heating_network_1.nodes[node]["pressure"] = pressure

    # The network is plotted using the show_3d function.

    vis = ug.Visuals(heating_network_1)
    fig = vis.show_3d(save_as=save_as, show_plot=False, label_size=30)


# Main function
if __name__ == "__main__":
    print("*** Strating plots ***")
    main()
    print("*** Done ***")
