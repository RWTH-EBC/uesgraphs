"""
This module contains unit tests for uesgraphs systemmodels module
"""

import pytest
import os
import tempfile
import shapely.geometry as sg
import logging

# Use direct import to avoid sklearn/scipy dependency issues (same hack as test_utilities.py)
import importlib.util
systemmodelheating_path = os.path.join(os.path.dirname(__file__), '..', 'uesgraphs', 'systemmodels', 'systemmodelheating.py')
spec = importlib.util.spec_from_file_location("systemmodelheating", systemmodelheating_path)
systemmodelheating = importlib.util.module_from_spec(spec)
spec.loader.exec_module(systemmodelheating)

# Extract the class
SystemModelHeating = systemmodelheating.SystemModelHeating


class TestSystemModelHeating:
    """Test class for SystemModelHeating functionality"""
    
    @pytest.fixture
    def basic_model(self):
        """Fixture providing a basic SystemModelHeating instance"""
        return SystemModelHeating()
    
    @pytest.fixture 
    def custom_model(self):
        """Fixture providing a custom SystemModelHeating instance"""
        return SystemModelHeating(model_name="TestModel", network_type="heating")
    
    def test_init_default_parameters(self, basic_model):
        """Test SystemModelHeating initialization with default parameters"""
        assert basic_model.model_name == "Test"
        assert basic_model.network_type == "heating"
        assert basic_model.solver == "Cvode"
        assert basic_model.stop_time is None
        assert basic_model.timestep is None
        assert basic_model.nodelist_pipe == []
        assert hasattr(basic_model, 'meta_data')
        assert isinstance(basic_model.meta_data, dict)
        assert hasattr(basic_model, 'version_info')
    
    def test_init_custom_parameters(self, custom_model):
        """Test SystemModelHeating initialization with custom parameters"""
        assert custom_model.model_name == "TestModel"
        assert custom_model.network_type == "heating"
        assert custom_model.solver == "Cvode"
        assert custom_model.nodelist_pipe == []
    
    def test_init_cooling_network(self):
        """Test SystemModelHeating initialization for cooling network"""
        cooling_model = SystemModelHeating(model_name="CoolingTest", network_type="cooling")
        assert cooling_model.model_name == "CoolingTest"
        assert cooling_model.network_type == "cooling"
    
    def test_medium_property_default(self, basic_model):
        """Test medium property default value"""
        assert basic_model.medium == "AixLib.Media.Water"
    
    def test_medium_property_setter(self, basic_model):
        """Test medium property setter with valid medium"""
        # Use a valid medium from the allowed list
        test_medium = "AixLib.Media.Specialized.Water.ConstantProperties_pT"
        basic_model.medium = test_medium
        assert basic_model.medium == test_medium
    
    def test_medium_property_invalid_value(self, basic_model):
        """Test medium property setter with invalid medium raises ValueError"""
        with pytest.raises(ValueError, match="Unknown Medium choice"):
            basic_model.medium = "Invalid.Medium.Type"
    
    def test_doc_string_property(self, basic_model):
        """Test doc_string property"""
        # Default doc_string is auto-generated with version info
        default_doc = basic_model.doc_string
        assert isinstance(default_doc, str)
        assert len(default_doc) > 0
        assert "uesgraphs version" in default_doc
        
        # Test setter
        test_doc = "This is a test documentation string"
        basic_model.doc_string = test_doc
        assert basic_model.doc_string == test_doc
    
    def test_time_property_with_values(self, basic_model):
        """Test time property calculation (from old test_uesmodel.py)"""
        basic_model.stop_time = 3600
        basic_model.timestep = 900
        
        expected_time = [0, 900, 1800, 2700, 3600]
        assert basic_model.time == expected_time
    
    def test_time_property_different_intervals(self, basic_model):
        """Test time property with different time intervals"""
        basic_model.stop_time = 1800  # 30 minutes
        basic_model.timestep = 300    # 5 minutes
        
        expected_time = [0, 300, 600, 900, 1200, 1500, 1800]
        assert basic_model.time == expected_time
    
    def test_time_property_no_values(self, basic_model):
        """Test time property when stop_time or timestep not set"""
        # When values are None, should return empty list
        assert basic_model.time == []
    
    def test_add_pipe_node_default(self, basic_model):
        """Test adding a pipe node with default parameters"""
        initial_count = len(basic_model.nodelist_pipe)
        
        basic_model.add_pipe_node()
        
        assert len(basic_model.nodelist_pipe) == initial_count + 1
        
        # Check that the node was actually added to the graph
        pipe_node = basic_model.nodelist_pipe[0]
        assert pipe_node in basic_model.nodes
    
    def test_add_pipe_node_with_name(self, basic_model):
        """Test adding a pipe node with custom name"""
        test_name = "test_pipe_node"
        
        basic_model.add_pipe_node(name=test_name)
        
        assert len(basic_model.nodelist_pipe) == 1
        pipe_node = basic_model.nodelist_pipe[0]
        assert basic_model.nodes[pipe_node]["name"] == test_name
    
    def test_add_pipe_node_with_position(self, basic_model):
        """Test adding a pipe node with custom position"""
        test_position = sg.Point(10.0, 20.0)
        
        basic_model.add_pipe_node(name="positioned_pipe", position=test_position)
        
        assert len(basic_model.nodelist_pipe) == 1
        pipe_node = basic_model.nodelist_pipe[0]
        assert basic_model.nodes[pipe_node]["position"].equals(test_position)
    
    def test_add_multiple_pipe_nodes(self, basic_model):
        """Test adding multiple pipe nodes"""
        names = ["pipe_1", "pipe_2", "pipe_3"]
        
        for name in names:
            basic_model.add_pipe_node(name=name)
        
        assert len(basic_model.nodelist_pipe) == 3
        
        # Verify all names are present
        node_names = []
        for pipe_node in basic_model.nodelist_pipe:
            node_names.append(basic_model.nodes[pipe_node]["name"])
        
        for name in names:
            assert name in node_names
    
    def test_remove_pipe_node(self, basic_model):
        """Test removing a pipe node (from old test_uesmodel.py)"""
        # First add a pipe node
        basic_model.add_pipe_node(name="test_pipe", position=sg.Point(0, 0))
        assert len(basic_model.nodelist_pipe) == 1
        
        # Get the node to remove
        pipe_node = basic_model.nodelist_pipe[0]
        
        # Remove it
        basic_model.remove_pipe_node(pipe_node)
        
        # Verify it's gone
        assert len(basic_model.nodelist_pipe) == 0
        assert pipe_node not in basic_model.nodes
    
    def test_remove_pipe_node_multiple(self, basic_model):
        """Test removing multiple pipe nodes"""
        # Add several pipe nodes
        for i in range(3):
            basic_model.add_pipe_node(name=f"pipe_{i}")
        
        assert len(basic_model.nodelist_pipe) == 3
        
        # Remove them one by one
        while basic_model.nodelist_pipe:
            pipe_node = basic_model.nodelist_pipe[0]
            basic_model.remove_pipe_node(pipe_node)
        
        assert len(basic_model.nodelist_pipe) == 0
    
    def test_nodes_by_name_attribute(self, basic_model):
        """Test that nodes_by_name attribute works correctly"""
        test_name = "named_pipe"
        basic_model.add_pipe_node(name=test_name)
        
        # Should be able to access node by name
        assert hasattr(basic_model, 'nodes_by_name')
        if hasattr(basic_model, 'nodes_by_name'):
            assert test_name in basic_model.nodes_by_name
            node_id = basic_model.nodes_by_name[test_name]
            assert node_id in basic_model.nodelist_pipe
    
    def test_solver_attribute(self, basic_model):
        """Test solver attribute is accessible and modifiable"""
        # Default solver
        assert basic_model.solver == "Cvode"
        
        # Change solver
        basic_model.solver = "Dassl"
        assert basic_model.solver == "Dassl"
    
    def test_meta_data_attribute(self, basic_model):
        """Test meta_data attribute functionality"""
        # Should start as empty dict
        assert isinstance(basic_model.meta_data, dict)
        assert len(basic_model.meta_data) == 0
        
        # Should be modifiable
        basic_model.meta_data["test_key"] = "test_value"
        assert basic_model.meta_data["test_key"] == "test_value"
    
    def test_networkx_inheritance(self, basic_model):
        """Test that SystemModelHeating properly inherits from NetworkX Graph"""
        # Should have NetworkX graph methods
        assert hasattr(basic_model, 'add_node')
        assert hasattr(basic_model, 'add_edge')
        assert hasattr(basic_model, 'nodes')
        assert hasattr(basic_model, 'edges')
        
        # Should be able to use NetworkX functionality
        basic_model.add_node("test_node", test_attr="test_value")
        assert "test_node" in basic_model.nodes
        assert basic_model.nodes["test_node"]["test_attr"] == "test_value"