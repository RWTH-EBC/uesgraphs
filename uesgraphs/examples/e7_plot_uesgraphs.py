"""This module includes tests and demonstrations of uesgraphs"""

import os
import random

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
    example_district = e2.simple_dhc_model()
    example_district = e3.add_more_networks(example_district)

    workspace = make_workspace('demo')

    scaling_factor = 10

    # Plot full network layout

    save_as = os.path.join(workspace, '01_district.png')
    vis = ug.Visuals(example_district)
    vis.show_network(save_as=save_as, show_plot=False,
                     scaling_factor=scaling_factor)

    # Plot heating network

    save_as = os.path.join(workspace, '02_heating_1.png')
    heating_network = example_district.create_subgraphs('heating')['default']
    vis_heating = ug.Visuals(heating_network)
    vis_heating.show_network(save_as=save_as, show_plot=False,
                             scaling_factor=scaling_factor)

    # Plot cooling network

    save_as = os.path.join(workspace, '03_cooling_1.png')
    cooling_network = example_district.create_subgraphs('cooling')['default']
    vis_cooling = ug.Visuals(cooling_network)
    vis_cooling.show_network(save_as=save_as, show_plot=False,
                             scaling_factor=scaling_factor)

    # Plot heating 2 network

    save_as = os.path.join(workspace, '04_heating_2.png')
    heating_network_2 = example_district.create_subgraphs(
        'heating')['heating_2']
    vis_heating_2 = ug.Visuals(heating_network_2)
    vis_heating_2.show_network(save_as=save_as, show_plot=False,
                               scaling_factor=scaling_factor)

    # Plot cooling 2 network

    save_as = os.path.join(workspace, '05_cooling_2.png')
    cooling_network_2 = example_district.create_subgraphs(
        'cooling')['cooling_2']
    vis_cooling_2 = ug.Visuals(cooling_network_2)
    vis_cooling_2.show_network(save_as=save_as, show_plot=False,
                               scaling_factor=scaling_factor)

    # Plot electricity network

    save_as = os.path.join(workspace, '06_electricity.png')
    electricity_network = example_district.create_subgraphs(
        'electricity')['default']
    vis_electricity = ug.Visuals(electricity_network)
    vis_electricity.show_network(save_as=save_as, show_plot=False,
                                 scaling_factor=scaling_factor)

    # Plot gas network

    save_as = os.path.join(workspace, '07_gas.png')
    gas_network = example_district.create_subgraphs('gas')['default']
    vis_gas = ug.Visuals(gas_network)
    vis_gas.show_network(save_as=save_as, show_plot=False,
                         scaling_factor=scaling_factor)

    # Plot other networks

    save_as = os.path.join(workspace, '08_others.png')
    others_network = example_district.create_subgraphs('others')['default']
    vis_others = ug.Visuals(others_network)
    vis_others.show_network(save_as=save_as, show_plot=False,
                            scaling_factor=scaling_factor)

    # Plot network in 3d layout

    save_as = os.path.join(workspace, '09_network_3d.png')
    vis = ug.Visuals(example_district)
    vis.network_explosion(save_as=save_as, show_plot=False, angle=250,
                          scaling_factor=scaling_factor * 5,
                          networks=[])

    # Plot network explosion

    save_as = os.path.join(workspace, '10_network_explosion.png')
    vis = ug.Visuals(example_district)
    vis.network_explosion(save_as=save_as, show_plot=False, angle=250,
                          scaling_factor=scaling_factor * 5)

    # Plot simple network visualization

    save_as = os.path.join(workspace, '11_simple.png')
    scaling_factor = 50
    vis = ug.Visuals(example_district)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        simple=True)

    # Plot diameters for two edges

    save_as = os.path.join(workspace, '12_diameters.png')
    random.seed(12345)
    heating_network_1 = example_district.create_subgraphs(
        network_type='heating', all_buildings=False)['default']
    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)
    for edge in edgelist_sorted:
        diameter = random.uniform(0.05, 0.5)
        print('diameter', diameter)
        heating_network_1.edges[edge[0], edge[1]]['diameter'] = diameter
    print(heating_network_1.edges(data=True))
    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        show_diameters=True)

    # Plot diameters scaling

    save_as = os.path.join(workspace, '13_diameters_scaling.png')
    random.seed(12345)
    heating_network_1 = example_district.create_subgraphs(
        network_type='heating',
        all_buildings=False,
    )['default']
    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)
    for edge in edgelist_sorted:
        diameter = random.uniform(0.05, 0.5)
        print('diameter', diameter)
        heating_network_1.edges[edge[0], edge[1]]['diameter'] = diameter
    print(heating_network_1.edges(data=True))
    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        scaling_factor_diameter=50,
        show_diameters=True)

    # Plot mass flows

    save_as = os.path.join(workspace, '14_mass_flows.png')
    random.seed(12345)
    heating_network_1 = example_district.create_subgraphs(
        network_type='heating',
        all_buildings=False,
    )['default']
    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)
    for edge in edgelist_sorted:
        flow = random.uniform(0.1, 1)
        heating_network_1.edges[edge[0], edge[1]]['mass_flow'] = flow
    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        show_mass_flows=True)

    # Plot temperatures

    save_as = os.path.join(workspace, '15_temperatures.png')
    random.seed(12345)
    heating_network_1 = example_district.create_subgraphs(
        network_type='heating',
        all_buildings=False,
    )['default']
    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)
    for edge in edgelist_sorted:
        flow = random.uniform(0.1, 1)
        heating_network_1.edges[edge[0], edge[1]]['mass_flow'] = flow
    nodelist = list(heating_network_1.nodes())
    nodelist_sorted = sorted(nodelist)
    for node in nodelist_sorted:
        temp = random.uniform(50, 100)
        heating_network_1.nodes[node]['temperature_supply'] = temp
    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        add_edge_temperatures=True,
        add_edge_flows=True,
        label_size=30)

    # Plot markers

    save_as = os.path.join(workspace, '16_markers.png')
    heating_network_1 = example_district.create_subgraphs(
        network_type='heating',
        all_buildings=False,
    )['default']
    edgelist = list(heating_network_1.edges())
    edgelist_tuples_sorted = []
    for edge in edgelist:
        edgelist_tuples_sorted.append(sorted(edge))
    edgelist_sorted = sorted(edgelist_tuples_sorted)
    for edge in edgelist_sorted:
        edge_to_mark = [edge[0], edge[1]]
        break
    nodelist = list(heating_network_1.nodes())
    nodelist_sorted = sorted(nodelist)
    node_to_mark = nodelist_sorted[2]
    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        save_as=save_as,
        show_plot=False,
        scaling_factor=scaling_factor,
        node_markers=[node_to_mark],
        edge_markers=[edge_to_mark],
        labels='name',
        label_size=25)

    # Plot real 3d

    save_as = os.path.join(workspace, '17_3D.png')
    random.seed(12345)
    heating_network_1 = example_district.create_subgraphs(
        network_type='heating',
        all_buildings=False,
    )['default']
    nodelist = list(heating_network_1.nodes())
    nodelist_sorted = sorted(nodelist)
    for node in nodelist_sorted:
        pressure = random.uniform(2e5, 3e5)
        heating_network_1.nodes[node]['pressure'] = pressure
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_3d(
        save_as=save_as,
        show_plot=False,
        label_size=30)


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
    print("*** Strating plots ***")
    main()
    print("*** Done ***")
