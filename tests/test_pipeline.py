# -*- coding: utf-8 -*-
"""
Tests for the new Excel-based model generation pipeline.

This module tests the connector handling system, parameter resolution,
and Excel type conversion functionality introduced in the new pipeline.
"""

import os
import pytest
import tempfile
from uesgraphs.systemmodels.model_generation_pipeline import (
    resolve_parameter_value,
    parse_template_parameters,
    load_component_parameters,
    uesgraph_to_modelica
)
from uesgraphs import UESGraph


class TestResolveParameterValue:
    """Tests for the resolve_parameter_value function."""

    def test_scalar_to_timeseries_conversion(self):
        """Test that scalar values are converted to constant time-series."""
        time_array = [0, 900, 1800, 2700]  # 4 timesteps

        result = resolve_parameter_value(
            value=353.15,
            component_data={},
            param_name='TIn',
            component_id='supply1',
            time_array=time_array,
            as_timeseries=True
        )

        assert result == [353.15, 353.15, 353.15, 353.15]
        assert len(result) == len(time_array)

    def test_reference_resolution(self):
        """Test that @references resolve to component attributes."""
        component_data = {
            'diameter': 0.15,
            'design_temp': 353.15,
            'name': 'supply1'
        }

        result = resolve_parameter_value(
            value='@diameter',
            component_data=component_data,
            param_name='d',
            component_id='supply1'
        )

        assert result == 0.15

    def test_reference_resolution_missing_attribute_raises_error(self):
        """Test that referencing non-existent attributes raises ValueError."""
        component_data = {'name': 'supply1'}

        with pytest.raises(ValueError, match="non-existent attribute"):
            resolve_parameter_value(
                value='@missing_attr',
                component_data=component_data,
                param_name='some_param',
                component_id='supply1'
            )

    def test_direct_value_passthrough(self):
        """Test that direct numeric values pass through unchanged."""
        result = resolve_parameter_value(
            value=100000.0,
            component_data={},
            param_name='pReturn',
            component_id='supply1'
        )

        assert result == 100000.0


class TestParseTemplateParameters:
    """Tests for template parameter parsing."""

    def test_parse_template_returns_three_tuples(self):
        """Test that parse_template_parameters returns (main, aux, connectors)."""
        # Use the actual SourceIdeal template
        main, aux, connectors = parse_template_parameters(
            'Supply',
            model_name='AixLib_Fluid_DistrictHeatingCooling_Supplies_OpenLoop_SourceIdeal'
        )

        # Check return structure
        assert isinstance(main, list)
        assert isinstance(aux, list)
        assert isinstance(connectors, list)

        # Verify expected parameters from SourceIdeal template
        assert 'pReturn' in main
        assert 'TReturn' in main
        assert 'allowFlowReversal' in aux
        assert 'TIn' in connectors
        assert 'dpIn' in connectors


class TestExcelTypeConversion:
    """Tests for Excel value type conversion."""

    def test_scientific_notation_conversion(self):
        """Test that scientific notation strings are converted to float."""
        # Use the real Excel file
        excel_path = 'uesgraphs/data/uesgraphs_parameters_template.xlsx'

        if not os.path.exists(excel_path):
            pytest.skip("Excel template file not found")

        params = load_component_parameters(excel_path, 'Supply')

        # Check that pReturn (which is '1e5' in Excel) is converted to float
        assert 'pReturn' in params
        assert isinstance(params['pReturn'], (int, float))
    
    def test_boolean_string_conversion(self):
        """Test that TRUE/FALSE strings are converted to bool."""
        excel_path = 'uesgraphs/data/uesgraphs_parameters_template.xlsx'

        if not os.path.exists(excel_path):
            pytest.skip("Excel template file not found")

        params = load_component_parameters(excel_path, 'Supply')

        # Check that allowFlowReversal (which is 'TRUE' in Excel) is converted to bool
        assert 'allowFlowReversal' in params
        assert isinstance(params['allowFlowReversal'], bool)
        assert isinstance(params['allowFlowReversal'], bool)

class TestE16IntegrationPipeline:
    """Integration test using e16 example data."""

    def test_e16_geojson_to_modelica_pipeline(self):
        """
        Test the complete pipeline from GeoJSON import to Modelica generation.
        """
        # Define all paths once
        data_dir = os.path.join('uesgraphs', 'data')
        data_examples_dir = os.path.join(data_dir, 'examples')
        geojson_dir = os.path.join(data_examples_dir, 'e15_geojson')
        
        # File paths
        network_geojson = os.path.join(geojson_dir, 'network.geojson')
        buildings_geojson = os.path.join(geojson_dir, 'buildings.geojson')
        supply_geojson = os.path.join(geojson_dir, 'supply.geojson')
        demands_heat = os.path.join(data_examples_dir, 'demands-heat.csv')
        demands_dhw = os.path.join(data_examples_dir, 'demands-dhw.csv')
        demands_cool = os.path.join(data_examples_dir, 'demands-cool.csv')
        ground_temps = os.path.join(data_examples_dir, 'ground_temps_hassel.csv')
        params_template = os.path.join(data_dir, 'uesgraphs_parameters_template.xlsx')
        
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
                
                # Step 2: Run pipeline
                uesgraph_to_modelica(
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
                
                # Check that Modelica files were generated - search recursively
                sim_dir = os.path.join(models_dir, sim_dirs[0])
                mo_files = []
                for root, dirs, files in os.walk(sim_dir):
                    mo_files.extend([f for f in files if f.endswith('.mo')])
                
                assert len(mo_files) > 0, f"No Modelica files were generated in {sim_dir}"
                print(f"✓ Test passed: Found {len(mo_files)} Modelica files")
                
            except Exception as e:
                pytest.fail(f"Pipeline failed: {e}")
            finally:
                # Close all loggers to release file handles
                import logging
                logging.shutdown()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
