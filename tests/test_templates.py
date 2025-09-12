# -*- coding: utf-8 -*-
"""
Tests for UESTemplates class functionality.

This module tests the core UESTemplates class functionality with focused,
meaningful tests that validate real behavior without over-mocking.
"""

import os
import tempfile
import pytest
from uesgraphs.systemmodels.templates import UESTemplates


def test_load_config_real_json():
    """Test that we can load the actual JSON config file from the repository"""
    # Use the real JSON file
    config_file = "data/templates/template_aixlib_components.json"
    
    # This should work without any mocking - it's just JSON parsing
    result = UESTemplates._load_config(config_file)
    
    # Expected models from the actual JSON file (hardcoded to prevent data loss)
    expected_models = {
        "AixLib.Fluid.DistrictHeatingCooling.Demands.ClosedLoop.DHCSubstationHeatPumpChiller",
        "AixLib.Fluid.DistrictHeatingCooling.Demands.ClosedLoop.DHCSubstationHeatPumpDirectCooling", 
        "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot",
        "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
        "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDpBypass",
        "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDpFixedTempDifferenceBypass",
        "AixLib.Fluid.DistrictHeatingCooling.Supplies.ClosedLoop.DHCSupplyHeaterCoolerStorage",
        "AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        "AixLib.Fluid.DistrictHeatingCooling.Pipes.DHCPipe",
        "AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded",
        "AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeZeta",
        "AixLib.Fluid.DistrictHeatingCooling.Pipes.StaticPipe"
    }
    
    # Test that we loaded the correct models
    assert len(result) == 3  # Should have Demand, Supply, Pipe
    assert "Demand" in result
    assert "Supply" in result  
    assert "Pipe" in result
    
    # Verify we got exactly the expected models
    all_models = set()
    for model_type, models in result.items():
        all_models.update(models)
    
    assert all_models == expected_models
    
    # Test specific counts from our JSON
    assert len(result["Demand"]) == 6
    assert len(result["Supply"]) == 2
    assert len(result["Pipe"]) == 4


def test_load_config_missing_file():
    """Test error handling for missing config file"""
    result = UESTemplates._load_config("nonexistent.json")
    
    # Should return empty dict, not crash
    assert result == {}


def test_bulk_methods_exist():
    """Test that new bulk methods are available on the class"""
    assert hasattr(UESTemplates, 'generate_bulk')
    assert hasattr(UESTemplates, 'generate_from_config') 
    assert hasattr(UESTemplates, '_load_config')
    assert hasattr(UESTemplates, '_auto_detect_aixlib')
    
    assert callable(UESTemplates.generate_bulk)
    assert callable(UESTemplates.generate_from_config)
    assert callable(UESTemplates._load_config)
    assert callable(UESTemplates._auto_detect_aixlib)


def test_constructor_basic_functionality():
    """Test UESTemplates constructor creates proper instance"""
    template = UESTemplates("AixLib.Test.Model", "Demand")
    
    assert template.model_name == "AixLib.Test.Model"
    assert template.model_type == "Demand"
    assert template.rigorous == False
    assert template.template_name == "AixLib_Test_Model.mako"
    assert template.template_directory.endswith("data/templates")


def test_template_file_operations():
    """Test template file save functionality works"""
    template = UESTemplates("AixLib.Test.Model", "Demand")
    
    with tempfile.NamedTemporaryFile(suffix=".mako", delete=False) as tmp_file:
        template.save_path = tmp_file.name
        sample_template = "<%def name='test'>Test template content</%def>"
        
        # Set rigorous mode to avoid interactive prompt
        template.rigorous = True
        
        template._save_to_mako(sample_template)
        
        # Verify file was created and contains expected content
        assert os.path.exists(tmp_file.name)
        
        with open(tmp_file.name, 'r') as f:
            content = f.read()
            assert "Test template content" in content
        
        # Cleanup
        os.unlink(tmp_file.name)


def test_integration_workflow_basic():
    """Test basic integration workflow - constructor to template generation"""
    # Test that we can create instances for all supported types
    demand_template = UESTemplates("AixLib.Test.Model", "Demand")
    supply_template = UESTemplates("AixLib.Test.Model", "Supply") 
    pipe_template = UESTemplates("AixLib.Test.Model", "Pipe")
    
    # Verify path construction works correctly
    assert "demand" in demand_template.save_path.lower()
    assert "supply" in supply_template.save_path.lower()
    assert "pipe" in pipe_template.save_path.lower()
    
    # Verify basic methods exist and are callable
    for template in [demand_template, supply_template, pipe_template]:
        assert hasattr(template, 'render')
        assert hasattr(template, '_check_template')
        assert callable(template.render)
        assert callable(template._check_template)
