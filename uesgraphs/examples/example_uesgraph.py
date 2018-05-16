"""This module includes tests and demonstrations of uesgraphs"""

import os
from shapely.geometry import Point
import uesgraphs as ug

import matplotlib.pyplot as plt


def main():
    # plot_example_networks()
    # street_nodes()
    # to_json()
    # additional_attrib()
    example_readme()


def example_readme():
    """The example given in the README.md file
    """
    workspace = make_workspace('readme')

    graph = ug.UESGraph()

    supply = graph.add_building(
        name='Supply',
        position=Point(0, 10),
        is_supply_heating=True,
    )
    demand = graph.add_building(
        name='Building 1',
        position=Point(50, 15),
    )
    heating_node = graph.add_network_node(
        network_type='heating',
        position=Point(30, 5),
    )

    graph.add_edge(supply, heating_node)
    graph.add_edge(heating_node, demand)

    save_as = os.path.join(workspace, 'graph.png')
    vis = ug.Visuals(graph)
    vis.show_network(
        save_as=save_as,
        scaling_factor=30,
    )


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


def add_more_networks(example_district):
    """Adds an electric grid to the simple_dhc_model example

    Parameters
    ----------
    example_district : uesgraphs.uesgraph.UESGraph object
        An UESGraph containing 4 buildings connected to 2 heating supplies and
        2 cooling supplies via 2 heating and cooling networks each from
        `simple_dhc_model()`

    Returns
    -------
    example_district : uesgraphs.uesgraph.UESGraph object
        An UESGraph containing 8 buildings and various supplies and networks
        to illustrate UESGraph use
    """
    building_1 = example_district.nodes_by_name['building_1']
    building_2 = example_district.nodes_by_name['building_2']
    building_3 = example_district.nodes_by_name['building_3']
    building_4 = example_district.nodes_by_name['building_4']

    # Add electricity network
    supply_electricity = example_district.add_building(
        position=Point(6, 2),
        is_supply_electricity=True,
    )
    en_1 = example_district.add_network_node(network_type='electricity',
                                             position=Point(5, 2.5))
    en_2 = example_district.add_network_node(network_type='electricity',
                                             position=Point(4, 2.5))
    en_3 = example_district.add_network_node(network_type='electricity',
                                             position=Point(3, 2.5))
    en_4 = example_district.add_network_node(network_type='electricity',
                                             position=Point(2, 2.5))
    example_district.add_edge(en_1, building_4)
    example_district.add_edge(en_2, building_3)
    example_district.add_edge(en_3, building_2)
    example_district.add_edge(en_4, building_1)
    example_district.add_edge(en_1, en_2)
    example_district.add_edge(en_2, en_3)
    example_district.add_edge(en_3, en_4)
    example_district.add_edge(en_1, supply_electricity)

    # Add more buildings supplied by gas and electricity
    building_5 = example_district.add_building(position=Point(7, 3))
    building_6 = example_district.add_building(position=Point(7, 4))
    building_7 = example_district.add_building(position=Point(7, 5))
    en_5 = example_district.add_network_node(network_type='electricity',
                                             position=Point(6.5, 3))
    en_6 = example_district.add_network_node(network_type='electricity',
                                             position=Point(6.5, 4))
    en_7 = example_district.add_network_node(network_type='electricity',
                                             position=Point(6.5, 5))
    example_district.add_edge(en_5, en_6)
    example_district.add_edge(en_6, en_7)
    example_district.add_edge(en_5, supply_electricity)
    example_district.add_edge(en_5, building_5)
    example_district.add_edge(en_6, building_6)
    example_district.add_edge(en_7, building_7)

    supply_gas = example_district.add_building(position=Point(8, 1),
                                               is_supply_gas=True)
    gn_1 = example_district.add_network_node(network_type='gas',
                                             position=Point(8, 3))
    gn_2 = example_district.add_network_node(network_type='gas',
                                             position=Point(8, 4))
    gn_3 = example_district.add_network_node(network_type='gas',
                                             position=Point(8, 5))
    example_district.add_edge(gn_1, gn_2)
    example_district.add_edge(gn_2, gn_3)
    example_district.add_edge(gn_1, supply_gas)
    example_district.add_edge(gn_1, building_5)
    example_district.add_edge(gn_2, building_6)
    example_district.add_edge(gn_3, building_7)

    # Add a network of type 'other'
    supply_other = example_district.add_building(position=Point(7.5, 7),
                                                 is_supply_other=True)
    on_1 = example_district.add_network_node(network_type='others',
                                             position=Point(7.5, 5))
    on_2 = example_district.add_network_node(network_type='others',
                                             position=Point(7.5, 4))
    example_district.add_edge(on_1, on_2)
    example_district.add_edge(on_1, supply_other)
    example_district.add_edge(on_1, building_7)
    example_district.add_edge(on_2, building_6)

    # Add street nodes
    sn_11 = example_district.add_street_node(position=Point(1, 2.5), block=1)
    sn_12 = example_district.add_street_node(position=Point(6, 2.5), block=1)
    sn_13 = example_district.add_street_node(position=Point(6, 3.5), block=1)
    sn_14 = example_district.add_street_node(position=Point(1, 3.5), block=1)

    sn_21 = example_district.add_street_node(position=Point(6, 5.5), block=2)
    sn_22 = example_district.add_street_node(position=Point(6, 2.5), block=2)
    sn_23 = example_district.add_street_node(position=Point(8, 2.5), block=2)
    sn_24 = example_district.add_street_node(position=Point(8, 5.5), block=2)

    example_district.add_edge(sn_11, sn_12)
    example_district.add_edge(sn_12, sn_13)
    example_district.add_edge(sn_13, sn_14)
    example_district.add_edge(sn_14, sn_11)

    example_district.add_edge(sn_21, sn_22)
    example_district.add_edge(sn_22, sn_23)
    example_district.add_edge(sn_23, sn_24)
    example_district.add_edge(sn_24, sn_21)

    return example_district


def plot_example_networks():
    """Plots example networks to demo uesgraphs
    """
    example_district = simple_dhc_model()
    example_district = add_more_networks(example_district)

    workspace = make_workspace('demo')
    
    scaling_factor = 10

    save_as = os.path.join(workspace, '01_District.png')
    vis = ug.Visuals(example_district)
    vis.show_network(save_as=save_as, show_plot=False,
                     scaling_factor=scaling_factor)

    save_as = os.path.join(workspace, '02_Heating_1.png')
    heating_network = example_district.create_subgraphs('heating')['default']
    vis_heating = ug.Visuals(heating_network)
    vis_heating.show_network(save_as=save_as, show_plot=False,
                             scaling_factor=scaling_factor)

    save_as = os.path.join(workspace, '03_Cooling_1.png')
    cooling_network = example_district.create_subgraphs('cooling')['default']
    vis_cooling = ug.Visuals(cooling_network)
    vis_cooling.show_network(save_as=save_as, show_plot=False,
                             scaling_factor=scaling_factor)

    save_as = os.path.join(workspace, '04_Heating_2.png')
    heating_network_2 = example_district.create_subgraphs('heating')[
                            'heating_2']
    vis_heating_2 = ug.Visuals(heating_network_2)
    vis_heating_2.show_network(save_as=save_as, show_plot=False,
                               scaling_factor=scaling_factor)

    save_as = os.path.join(workspace, '05_Cooling_2.png')
    cooling_network_2 = example_district.create_subgraphs('cooling')[
                            'cooling_2']
    vis_cooling_2 = ug.Visuals(cooling_network_2)
    vis_cooling_2.show_network(save_as=save_as, show_plot=False,
                               scaling_factor=scaling_factor)

    save_as = os.path.join(workspace, '06_Electricity.png')
    electricity_network = example_district.create_subgraphs('electricity')[
                            'default']
    vis_electricity = ug.Visuals(electricity_network)
    vis_electricity.show_network(save_as=save_as, show_plot=False,
                                 scaling_factor=scaling_factor)

    save_as = os.path.join(workspace, '07_Gas.png')
    gas_network = example_district.create_subgraphs('gas')['default']
    vis_gas = ug.Visuals(gas_network)
    vis_gas.show_network(save_as=save_as, show_plot=False,
                         scaling_factor=scaling_factor)

    save_as = os.path.join(workspace, '08_Others.png')
    others_network = example_district.create_subgraphs('others')['default']
    vis_others = ug.Visuals(others_network)
    vis_others.show_network(save_as=save_as, show_plot=False,
                            scaling_factor=scaling_factor)


    save_as = os.path.join(workspace, '09_Network_3d.png')
    vis = ug.Visuals(example_district)
    vis.network_explosion(save_as=save_as, show_plot=False, angle=250,
                          scaling_factor=scaling_factor*5,
                          networks=[])


    save_as = os.path.join(workspace, '10_Network_Explosion.png')
    vis = ug.Visuals(example_district)
    vis.network_explosion(save_as=save_as, show_plot=False, angle=250,
                          scaling_factor=scaling_factor*5)

def to_json():
    """Demos the output of an uesgraph to JSON
    """
    workspace = make_workspace('json_output')

    example_district = simple_dhc_model()
    example_district.to_json(path=workspace,
                             name='demo')


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
    main()
