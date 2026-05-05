# -*- coding: utf-8 -*-
"""
Tests for the new pandapipes integration with simulations.

This module tests the Excel type conversion functionality and the pandapipes pipeline.
"""

import os
import pytest
import tempfile
from pathlib import Path
import os
import uesgraphs as ug
import uesgraphs.uesmodels.utilities.uesgenerator as uesgen
import uesgraphs.uesmodels.utilities.utilities as utils

class TestUESModelsUtilities:
    """Integration test using e9, which should cover most of uesgenerator utilities."""

    def test_e9(self):
        """
        Test the complete example e9.
        """
        # Define all paths once
        BASE = Path(__file__).resolve().parents[1]
        data_dir = BASE / "uesgraphs" / "data"
        abs_file = data_dir / "campus_melaten.osm"

        if not os.path.exists(abs_file):
            pytest.skip(f"Required file not found: {abs_file}")
        
        # Create temporary workspace - ignore cleanup errors on Windows
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as workspace:
            try:
                example_district = ug.UESGraph()
                
                example_district.from_osm(
                    osm_file=abs_file,
                    name="Melaten",
                    check_boundary=False,
                    transform_positions=True,
                )

                # Generate a urban energy system using the 'UESGenerator' and the data just
                # created from OSM file.

                uesgenerator = uesgen.UESGenerator()
                uesgenerator.uesgraph = example_district

                # Find street crossings

                uesgenerator.find_crossings()

                # Cluster buildings for a more generic usage using the cluster_bldg
                # function. The parameter 'eps' indicates the maximum distance (in m) that
                # points can be away from each other to be considered a cluster.
                assert utils.cluster_bldg(uesgenerator, eps=50), "cluster_bldg failed"

                # Adds the network to the district based on the street layout using
                # add_network_new function. There are three parameters to set. 'supply_node'
                # specifies the heating supply building. 'number_of_buildings' gives
                # the number of buildings to be connected to the heating network and
                # 'success_rate' indicates the probability of a building to be part of the
                # heating network.

                supply_node = None

                for node in example_district.nodelist_building:
                    node_data = example_district.nodes[node]

                    if node_data.get('osm_id') == '87275925':
                        node_data['is_supply_heating'] = True
                        supply_node = node

                assert uesgenerator.add_network_new(
                    supply_node=supply_node,
                    number_of_buildings=len(example_district.nodelist_building),
                    success_rate=1.0,
                    workspace=workspace,
                    ), "add_network_new failed"

            except Exception as e:
                pytest.fail(f"UESModels example failed: {e}")
            finally:
                # Close all loggers to release file handles
                import logging
                logging.shutdown()


