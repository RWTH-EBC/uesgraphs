# -*- coding: utf-8 -*-
"""
Tests for the TEASER and OpenDHW integration.

This module tests if TEASER and OpenDHW are able to generate the expected demand profiles 
with the provided GeoJSON, so that the installation of TEASER and OpenDHW is verified.
"""

import os
import pytest
import tempfile
from uesgraphs.DHW_estimation.utilities import generate_DHW_profiles_from_geojson
from uesgraphs.teaser_integration.utilities import run_sim_teaser
# Close all loggers to release file handles
import logging

class TestE17IntegrationTEASER_OpenDHW:
    """Integration test using example e17."""

    def test_e17_TEASER_OpenDHW(self):
        """
        Test the TEASER and OpenDHW integrations.
        """

        # Define all paths once
        data_dir = os.path.join('uesgraphs', 'data')
        data_examples_dir = os.path.join(data_dir, 'examples')
        geojson_dir = os.path.join(data_examples_dir, 'e15_geojson')
        
        # File paths
        network_geojson = os.path.join(geojson_dir, 'network.geojson')
        buildings_geojson = os.path.join(geojson_dir, 'buildings_teaser_OpenDHW_info.geojson')
        supply_geojson = os.path.join(geojson_dir, 'supply.geojson')
        ground_temps = os.path.join(data_examples_dir, 'ground_temps_hassel.csv')
        params_template = os.path.join(data_dir, 'uesgraphs_parameters_template_pp.xlsx')
        
        # Check if all required files exist
        required_files = [
            network_geojson, buildings_geojson, supply_geojson,
            ground_temps, params_template
        ]
        for file_path in required_files:
            if not os.path.exists(file_path):
                pytest.skip(f"Required file not found: {file_path}")
        
        # Create temporary workspace - ignore cleanup errors on Windows
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as workspace:
            try:                
                # Step 1: Run TEASER simulations
                input_heating, input_cooling = run_sim_teaser(buildings_info_path=buildings_geojson,
                   save_path=workspace,
                   sim_setup_path=params_template,
                   log_level=logging.INFO,
                   number_of_workers=1
                   )
                
                # Step 2: Verify output
                demands_dir = os.path.join(workspace, 'demand_csv')
                assert os.path.exists(demands_dir), "Demand estimation directory was not created"
                
                # Check that demand estimation files were generated
                csv_files = []
                for root, dirs, files in os.walk(demands_dir):
                    csv_files.extend([f for f in files if f.endswith('.csv')])
                
                assert len(csv_files) > 0, f"Not all files were generated in {demands_dir}"
                print(f"✓ Test passed: Found {len(csv_files)} CSV files")
                
            except Exception as e:
                pytest.fail(f"TEASER failed: {e}")
            
            try:
                # Step 1: Run OpenDHW for generations
                input_dhw = generate_DHW_profiles_from_geojson(buildings_info_path=buildings_geojson,
                   save_path=workspace,
                   sim_setup_path=params_template,
                   log_level=logging.INFO
                   )

                # Step 2: Verify output
                demands_dir = os.path.join(workspace, 'demand_csv')
                assert os.path.exists(demands_dir), "Demand estimation directory was not created"
                
                # Check that demand estimation files were generated
                csv_files = []
                for root, dirs, files in os.walk(demands_dir):
                    csv_files.extend([f for f in files if f.endswith('.csv')])
                
                assert len(csv_files) > 2, f"Not all csv files were generated in {demands_dir}"
                print(f"✓ Test passed: Found {len(csv_files)} CSV files")
                
            except Exception as e:
                pytest.fail(f"OpenDHW failed: {e}")
            finally:
                # Close all loggers to release file handles
                logging.shutdown()


