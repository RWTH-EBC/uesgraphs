"""This module includes tests and demonstrations of uesgraphs"""

import os
from shapely.geometry import Point
import uesgraphs as ug
import uesgraphs.utilities as ut
import matplotlib.pyplot as plt


def main():
    simple_dhc_model()


def simple_dhc_model():
    """Initializes an UESGraph object, adds 2 heating and cooling networks each

    Returns
    -------
    example_district : uesgraphs.uesgraph.UESGraph object
        An UESGraph containing 4 buildings connected to 2 heating supplies and
        2 cooling supplies via 2 heating and cooling networks each
    """
    example_district = ug.UESGraph()

    # To generate a building the function example_district.add_building is
    # used. Nine parameters are available. The name and the position of the
    # building node need to be set. If the building should be a supply station
    # this can be set by one of the following parameters: is_supply_heating,
    # is_supply_cooling, is_supply_electricity, is_supply_gas and
    # is_supply_other. Below one heating and one cooling supply building is
    # generated.

    supply_heating_1 = example_district.add_building(
        position=Point(1, 2), is_supply_heating=True
    )
    supply_cooling_1 = example_district.add_building(
        position=Point(1, 1), is_supply_cooling=True
    )

    # Demand buildings are generated using the add_building function.

    building_1 = example_district.add_building(name="building_1", position=Point(2, 3))
    building_2 = example_district.add_building(name="building_2", position=Point(3, 3))
    building_3 = example_district.add_building(name="building_3", position=Point(4, 3))
    building_4 = example_district.add_building(name="building_4", position=Point(5, 3))

    # To generate a network node the function example_district.add_network_node
    # is used. A network node should not be placed at positions where there is
    # already a node of the same network or a building node. Eight parameters
    # are available. network_type defines the network into which to add the
    # node. The position is compulsory. Below two network nodes for a heating
    # network are added.

    hn_1 = example_district.add_network_node(
        network_type="heating", position=Point(2, 2)
    )
    hn_2 = example_district.add_network_node(
        network_type="heating", position=Point(3, 2)
    )

    # To connect the different nodes example_district.add_edge is used. Below
    # the heat supply building is connected to building_1, building_2 and
    # heat network nodes.

    example_district.add_edge(supply_heating_1, hn_1)
    example_district.add_edge(hn_1, building_1)
    example_district.add_edge(hn_1, hn_2)
    example_district.add_edge(hn_2, building_2)

    # Generating a cooling network node using add_network_node function.

    cn_1 = example_district.add_network_node(
        network_type="cooling", position=Point(3, 1)
    )

    # Connecting the cooling supply building to the cooling network node and
    # building_2.

    example_district.add_edge(supply_cooling_1, cn_1)
    example_district.add_edge(cn_1, building_2)

    # To generate a new network of a specified type
    # example_district.add_network is used. One can chose between the network
    # types: heating, cooling, electricity, gas and other. As second parameter
    # the name of the network has to be given. Below two networks are created,
    # one heating network called heating_2 and a cooling network called
    # cooling_2.

    example_district.add_network("heating", "heating_2")
    example_district.add_network("cooling", "cooling_2")

    # A second heat supply building and a second cooling supply building are
    # added using the example_district.add_building function.

    supply_heating_2 = example_district.add_building(
        position=Point(1, 4), is_supply_heating=True
    )
    supply_cooling_2 = example_district.add_building(
        position=Point(1, 5), is_supply_cooling=True
    )

    # A network node of the type `heating` is added to the network `heating_2`
    # using the example_district.add_network_node function.

    hn_3 = example_district.add_network_node(
        network_type="heating", position=Point(4, 4), network_id="heating_2"
    )

    # Afterwards the building `supply_heating_2` is connected to the heating
    # node `hn_3` and this one is connected to `building_3`.

    example_district.add_edge(supply_heating_2, hn_3)
    example_district.add_edge(hn_3, building_3)

    # A network node of the type `cooling` is added to the network `cooling_2`
    # using the example_district.add_network_node function.

    cn_2 = example_district.add_network_node(
        network_type="cooling", position=Point(2, 5), network_id="cooling_2"
    )

    # The building `supply_cooling_2` is connected to the cooling node `cn_2`
    # and this one is connected to building_1.

    example_district.add_edge(supply_cooling_2, cn_2)
    example_district.add_edge(cn_2, building_1)

    # A network node of the type `cooling` is added to the network `cooling_2`
    # using the example_district.add_network_node function.

    cn_3 = example_district.add_network_node(
        network_type="cooling", position=Point(5, 5), network_id="cooling_2"
    )

    # The cooling network node `cn_2` is connected to the cooling network node
    # `cn_3`. The building `building_4` is connected to `cn_3` using
    # example_district.add_edge function.

    example_district.add_edge(cn_2, cn_3)
    example_district.add_edge(cn_3, building_4)

    return example_district


# Main function
if __name__ == "__main__":
    print("*** Generating simple dhc graph ***")
    main()
    print("*** Done ***")
