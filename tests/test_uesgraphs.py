"""
This module contains unit tests for uesgraphs module
"""

import uesgraphs as ug
import math
import shapely.geometry as sg


class Test_uesgraphs(object):

    def test_add_building(self):
        """Initializes a graph and adds a building
        """
        origin = sg.Point(0, 0)

        test_graph = ug.UESGraph()
        test_graph.add_building()

        assert len(test_graph.nodelist_building) == 1

        test_graph.add_building(name='at_origin', position=origin)

        assert len(test_graph.nodelist_building) == 2

        names = []
        for node in test_graph.nodelist_building:
            names.append(test_graph.node[node]['name'])
        assert 'at_origin' in names

    def test_subgraphs(self):
        """Creates subgraphs for heating and cooling networks

        Verifies the subgraph creation for `all_buildings = True` and
        `all_buildings = False`
        """
        example_district = ug.simple_dhc_model()

        heating_network_0 = example_district.create_subgraphs('heating')[
            'default']
        heating_network_1 = example_district.create_subgraphs('heating')[
            'heating_2']

        cooling_network_0 = example_district.create_subgraphs('cooling')[
            'default']
        cooling_network_1 = example_district.create_subgraphs('cooling')[
            'cooling_2']

        assert (len(heating_network_0.nodelist_building) == 8)
        assert (len(heating_network_1.nodelist_building) == 8)
        assert (len(cooling_network_0.nodelist_building) == 8)
        assert (len(cooling_network_1.nodelist_building) == 8)

        heating_network_0 = example_district.create_subgraphs('heating',
                                            all_buildings=False)['default']
        heating_network_1 = example_district.create_subgraphs('heating',
                                            all_buildings=False)['heating_2']

        cooling_network_0 = example_district.create_subgraphs('cooling',
                                            all_buildings=False)['default']
        cooling_network_1 = example_district.create_subgraphs('cooling',
                                            all_buildings=False)['cooling_2']

        assert (len(heating_network_0.nodelist_building) == 3)
        assert (len(heating_network_1.nodelist_building) == 2)
        assert (len(cooling_network_0.nodelist_building) == 2)
        assert (len(cooling_network_1.nodelist_building) == 3)

    def test_subgraph_buildings(self):
        """Tests the subgraph setting None to export only buildings in a graph
        """
        example_district = ug.simple_dhc_model()

        building_graph = example_district.create_subgraphs(None)['default']
        assert len(building_graph.nodes()) == 8
        assert len(building_graph.edges()) == 0

    def test_plot_example_networks(self):
        """Runs the example network plotting to make sure example works
        """
        ug.plot_example_networks()

    def test_additional_attribs(self):
        """Runs the additional attribute demo to make sure the example works
        """
        ug.additional_attrib()

    def test_remove_network_node(self):
        """
        Test method to remove network node from uesgraph object
        """
        test_graph = ug.UESGraph()

        position_1 = sg.Point(0, 0)
        test_graph.add_building(position=position_1)

        position_2 = sg.Point(10, 10)
        test_graph.add_network_node(network_type='heating',
                                    position=position_2)
        position_3 = sg.Point(20, 20)
        node_number = test_graph.add_network_node(network_type='heating',
                                                  position=position_3)

        position_4 = sg.Point(30, 30)
        test_graph.add_network_node(network_type='cooling',
                                    position=position_4)

        list_of_nodes = list(test_graph.nodes(data=False))
        assert list_of_nodes == [1001, 1002, 1003, 1004]

        test_graph.remove_network_node(node_number=node_number)

        list_of_nodes = list(test_graph.nodes(data=False))
        assert list_of_nodes == [1001, 1002, 1004]

    def test_calc_angle(self):
        """Tests the outputs of calc_angle() method in uesgraph
        """
        test_graph = ug.UESGraph()

        origin = sg.Point(0.0, 0.0)
        a = sg.Point(1.0, 1.0)
        b = sg.Point(0.0, 1.0)
        c = sg.Point(-1.0, 0.0)
        d = sg.Point(0.0, -1.0)

        assert test_graph.calc_angle(a, a, output='rad') == 0
        assert test_graph.calc_angle(a, a, output='degrees') == 0

        assert (test_graph.calc_angle(origin, b, output='rad') -
                math.pi / 2) < 1e-9
        assert test_graph.calc_angle(origin, b, output='degrees') == 90

        assert (test_graph.calc_angle(origin, c, output='rad') -
                math.pi) < 1e-9
        assert test_graph.calc_angle(origin, c, output='degrees') == 180

        assert (test_graph.calc_angle(origin, d, output='rad') -
                math.pi * 3 / 2) < 1e-9
        assert test_graph.calc_angle(origin, d, output='degrees') == 270

    def test_get_node_by_position(self):
        """Tests the get_node_by_position() method
        """
        #  Initialize graph
        uesgraph = ug.UESGraph()

        position_1 = sg.Point(0, 0)

        result_dict = uesgraph.get_node_by_position(position=position_1)
        assert result_dict == {}  # Empty dictionary

        #  Add building node
        uesgraph.add_building(name='building_1', position=position_1)

        #  Get node_id on position_1
        result_dict = uesgraph.get_node_by_position(position=position_1)
        assert result_dict == {1001: 'building_1'}  # Single building

        #  Add second building node add same position
        uesgraph.add_building(name='building_2', position=position_1)

        #  Get node_id on position_1
        result_dict = uesgraph.get_node_by_position(position=position_1)
        #  Two buildings on position 1
        assert result_dict == {1001: 'building_1', 1002: 'building_2'}

    def test_remove_unconnected_nodes(self):
        """Tests the remove_unconnected_nodes() method
        """
        example_district = ug.simple_dhc_model()

        lone_heating_node = example_district.add_network_node(
            network_type='heating',
            position=sg.Point(10, 10),
        )

        removed = example_district.remove_unconnected_nodes('heating',
                                                            'default')

        assert removed == [1015], 'Removal of unconnected node unsuccessful'

    def test_remove_dead_ends(self):
        """Tests the remove_dead_ends() method
        """
        example_district = ug.simple_dhc_model()

        dead_end_heating_node = example_district.add_network_node(
            network_type='heating',
            position=sg.Point(10, 10),
        )

        example_district.add_edge(1008, dead_end_heating_node)

        removed = example_district.remove_dead_ends('heating',
                                                    'default')

        msg = 'Removal of dead ends unsuccessful'
        assert len(example_district.edges()) == 12, msg
        assert removed == [1015], msg

