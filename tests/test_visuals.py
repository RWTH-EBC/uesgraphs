"""
This module contains test for the Visuals class of uesgraphs
"""


import pytest
import random
import sys

import uesgraphs as ug


@pytest.fixture(scope='module')
def example_district():
    """Provides the example district for each test
    """
    example_district = ug.simple_dhc_model()
    example_district = ug.add_more_networks(example_district)

    return example_district


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='01_district.png',
                               savefig_kwargs={'dpi': 150})
def test_basic_plot(example_district):
    """Tests a first plot with pytest-mpl

    Generated with `py.test --mpl-generate-path=tests/baseline_images`
    """
    scaling_factor = 10
    vis = ug.Visuals(example_district)
    fig = vis.show_network(
        show_plot=False,
        scaling_factor=scaling_factor,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='02_heating.png',
                               savefig_kwargs={'dpi': 150})
def test_heating_network(example_district):
    """Tests the plotting of an extracted heating network subgraph
    """
    heating_network_1 = example_district.create_subgraphs('heating')['default']

    scaling_factor = 10
    vis = ug.Visuals(heating_network_1)
    fig = vis.show_network(
        show_plot=False,
        scaling_factor=scaling_factor,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='03_cooling.png',
                               savefig_kwargs={'dpi': 150})
def test_cooling_network_2(example_district):
    """Tests the plotting of an extracted cooling network subgraph
    """
    cooling_network_2 = example_district.create_subgraphs('cooling')[
        'cooling_2']

    scaling_factor = 10
    vis = ug.Visuals(cooling_network_2)
    fig = vis.show_network(
        show_plot=False,
        scaling_factor=scaling_factor,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='04_electricity.png',
                               savefig_kwargs={'dpi': 150})
def test_electricity_network(example_district):
    """Tests the plotting of an extracted electricity network subgraph
    """
    electricity_network = example_district.create_subgraphs('electricity')[
                            'default']

    scaling_factor = 10
    vis = ug.Visuals(electricity_network)
    fig = vis.show_network(
        show_plot=False,
        scaling_factor=scaling_factor,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='05_gas.png',
                               savefig_kwargs={'dpi': 150})
def test_gas_network(example_district):
    """Tests the plotting of an extracted gas network subgraph
    """
    gas_network = example_district.create_subgraphs('gas')['default']

    scaling_factor = 10
    vis = ug.Visuals(gas_network)
    fig = vis.show_network(
        show_plot=False,
        scaling_factor=scaling_factor,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='06_others.png',
                               savefig_kwargs={'dpi': 150})
def test_others_network(example_district):
    """Tests the plotting of an extracted others network subgraph
    """
    others_network = example_district.create_subgraphs('others')['default']

    scaling_factor = 10
    vis = ug.Visuals(others_network)
    fig = vis.show_network(
        show_plot=False,
        scaling_factor=scaling_factor,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='07_network_explosion_base.png',
                               savefig_kwargs={'dpi': 150})
def test_network_explosion_base(example_district):
    """Tests the plotting of a network explosion drawing for base layer
    """
    scaling_factor = 50
    vis = ug.Visuals(example_district)
    fig = vis.network_explosion(
        show_plot=False,
        angle=250,
        scaling_factor=scaling_factor,
        networks=[],
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='08_network_explosion_all.png',
                               savefig_kwargs={'dpi': 150})
def test_network_explosion_all(example_district):
    """Tests the plotting of a network explosion drawing for all layers
    """
    scaling_factor = 50
    vis = ug.Visuals(example_district)
    fig = vis.network_explosion(
        show_plot=False,
        angle=250,
        scaling_factor=scaling_factor,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='09_simple.png',
                               savefig_kwargs={'dpi': 150})
def test_simple_plot(example_district):
    """Tests the plotting with simple set to True
    """
    scaling_factor = 50
    vis = ug.Visuals(example_district)
    fig = vis.show_network(
        show_plot=False,
        scaling_factor=scaling_factor,
        simple=True,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='10_diameters.png',
                               savefig_kwargs={'dpi': 150})
def test_diameters(example_district):
    """Tests the plotting of diameters with line thickness
    """
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
        show_plot=False,
        scaling_factor=scaling_factor,
        show_diameters=True,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='10_diameters_scaling.png',
                               savefig_kwargs={'dpi': 150})
def test_diameters_scaling(example_district):
    """Tests the plotting of diameters with line thickness
    """
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
        show_plot=False,
        scaling_factor=scaling_factor,
        scaling_factor_diameter=50,
        show_diameters=True,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='11_mass_flows.png',
                               savefig_kwargs={'dpi': 150})
def test_mass_flows(example_district):
    """Tests the plotting of mass flow rates with line thickness
    """
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
        show_plot=False,
        scaling_factor=scaling_factor,
        show_mass_flows=True,
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='12_temperatures.png',
                               savefig_kwargs={'dpi': 150})
def test_temperatures(example_district):
    """Tests the plotting of temperatures with line colors
    """
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
        show_plot=False,
        scaling_factor=scaling_factor,
        add_edge_temperatures=True,
        add_edge_flows=True,
        label_size=30
    )
    return fig


@pytest.mark.skipif(sys.version_info < (3, 6),
                    reason="The labeling of nodes will vary for Python 2")
@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='13_markers.png',
                               savefig_kwargs={'dpi': 150})
def test_markers(example_district):
    """Tests marking a node and an edge
    """
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
        show_plot=False,
        scaling_factor=scaling_factor,
        node_markers=[node_to_mark],
        edge_markers=[edge_to_mark],
        labels='name',
        label_size=30
    )
    return fig


@pytest.mark.mpl_image_compare(baseline_dir='baseline_images',
                               filename='14_3D.png',
                               savefig_kwargs={'dpi': 150})
def test_3D(example_district):
    """Tests the 3D plot
    """
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
        show_plot=False,
        label_size=30,
    )
    return fig
