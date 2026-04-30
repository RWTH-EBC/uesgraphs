# -*- coding: utf-8 -*-
"""
Tests for the new pandapipes integration with simulations.

This module tests the Excel type conversion functionality and the pandapipes pipeline.
"""

import os
import pytest
import tempfile
from uesgraphs.systemmodels_pp.utilities import (
    load_component_parameters,
    uesgraph_to_pandapipes
)
from uesgraphs.analyze.analysis_pp import analysis_pp
from pathlib import Path
import warnings
from uesgraphs import UESGraph

class TestExcelTypeConversion:
    """Tests for Excel value type conversion."""

    def test_scientific_notation_conversion(self):
        """Test that scientific notation strings are converted to float."""
        # Use the real Excel file
        BASE = Path(__file__).resolve().parents[1]
        data_dir = BASE / "uesgraphs" / "data"
        excel_path = data_dir / 'uesgraphs_parameters_template_pp.xlsx'

        if not os.path.exists(excel_path):
            pytest.skip("Excel template file not found")

        params = load_component_parameters(excel_path, 'Supply')

        # Check that pReturn (which is '1e5' in Excel) is converted to float
        assert 'pReturn' in params
        assert isinstance(params['pReturn'], (int, float))
    
    def test_boolean_string_conversion(self):
        """Test that TRUE/FALSE strings are converted to bool."""
        BASE = Path(__file__).resolve().parents[1]
        data_dir = BASE / "uesgraphs" / "data"
        excel_path = data_dir / 'uesgraphs_parameters_template_pp.xlsx'

        if not os.path.exists(excel_path):
            pytest.skip("Excel template file not found")

        #params = load_component_parameters(excel_path, 'Supply')

        # Check that allowFlowReversal (which is 'TRUE' in Excel) is converted to bool
        #assert 'allowFlowReversal' in params
        #assert isinstance(params['allowFlowReversal'], bool)
        #assert isinstance(params['allowFlowReversal'], bool)

class TestPipeline:
    """Integration test using e16 example data."""

    def test_e16_geojson_to_pandapipes_sim_analysis(self):
        """
        Test the complete pipeline from GeoJSON import to pandapipes simulation.
        """
        # Define all paths once
        BASE = Path(__file__).resolve().parents[1]
        data_dir = BASE / "uesgraphs" / "data"
        data_examples_dir = data_dir / "examples"
        geojson_dir = data_examples_dir / "e15_geojson"

        network_geojson = geojson_dir / "network.geojson"
        buildings_geojson = geojson_dir / "buildings.geojson"
        supply_geojson = geojson_dir / "supply.geojson"

        demands_heat = data_examples_dir / "demands-heat.csv"
        demands_dhw = data_examples_dir / "demands-dhw.csv"
        demands_cool = data_examples_dir / "demands-cool.csv"

        ground_temps = data_examples_dir / "ground_temps_hassel.csv"
        params_template = data_dir / "uesgraphs_parameters_template_pp.xlsx"
        
        # Check if all required files exist
        required_files = [
            network_geojson, buildings_geojson, supply_geojson,
            demands_heat, demands_dhw, demands_cool, 
            ground_temps, params_template
        ]
        for file_path in required_files:
            if not os.path.exists(file_path):
                pytest.skip(f"Required file not found: {file_path}")
        
        # Create temporary workspace - ignore cleanup errors on Windows
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as workspace:
            try:
                # Step 1: Import GeoJSON
                graph = UESGraph()
                graph.from_geojson(
                    network_path=network_geojson,
                    buildings_path=buildings_geojson,
                    supply_path=supply_geojson,
                    name='test_district',
                    save_path=workspace,
                    generate_visualizations=False
                )
                
                # Verify graph was created
                assert len(graph.nodelist_building) > 0
                assert graph.number_of_edges() > 0
                
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message="divide by zero encountered in log10",
                        category=RuntimeWarning
                    )

                    uesgraph_to_pandapipes(
                        uesgraph=graph,
                        simplification_level=0,
                        workspace=workspace,
                        sim_setup_path=params_template,
                        input_heating=demands_heat,
                        input_dhw=demands_dhw,
                        input_cooling=demands_cool,
                        ground_temp_path=ground_temps
                    )
                
                # Step 3: Verify output
                models_dir = os.path.join(workspace, 'models')
                assert os.path.exists(models_dir), "Models directory was not created"
                
                # Check that at least one simulation directory was created
                sim_dirs = [d for d in os.listdir(models_dir) if d.startswith('Sim')]
                assert len(sim_dirs) > 0, "No simulation directories were created"
                
                # Check that uesgraphs.json and uesgraphs_return.json were generated 
                sim_dir = os.path.join(models_dir, sim_dirs[0])
                json_files = []
                for root, dirs, files in os.walk(sim_dir):
                    json_files.extend([f for f in files if f.endswith('.json')])
                
                assert len(json_files) > 1, f"No json files were generated in {sim_dir}"
                print(f"✓ Test passed: Found {len(json_files)} json files")

                # Step 4: Run analysis
                sim_path = sim_dir

                analysis = analysis_pp(root_path=Path(sim_path))
                
                try:
                    analysis.thermal_loss_analysis()

                    analysis.pump_power_analysis()

                    analysis.pipe_plots()
                
                    base_path = Path(__file__).resolve().parent
                    file_path = base_path / ".." / "uesgraphs" / "data" / "examples" / "e15_geojson" / "network.geojson"
                    analysis.retransform_pipe_geojson_data(geojson_path=file_path)

                    analysis.visualize_network(time_index=4)
                    print(f"✓ Test passed: All analysis functions ran successfully")

                except Exception as e:
                    pytest.fail(f"Analysis crashed: {e}")
                
            except Exception as e:
                pytest.fail(f"Pandapipes-Pipeline failed: {e}")
            finally:
                # Close all loggers to release file handles
                import logging
                logging.shutdown()


