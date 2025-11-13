"""
This module contains unit tests for uesgraphs utilities module
"""

import pytest
import os
import tempfile
import shutil
import logging
import sys
from pathlib import Path

# HACK: Direct module import to avoid sklearn/scipy dependency conflicts
# This bypasses the normal uesgraphs package import chain that triggers sklearn
utilities_path = os.path.join(os.path.dirname(__file__), '..', 'uesgraphs', 'utilities.py')
import importlib.util
spec = importlib.util.spec_from_file_location("utilities", utilities_path)
utilities = importlib.util.module_from_spec(spec)
spec.loader.exec_module(utilities)

# Extract functions from the direct module import
default_json_path = utilities.default_json_path
make_workspace = utilities.make_workspace  
name_uesgraph = utilities.name_uesgraph
set_up_terminal_logger = utilities.set_up_terminal_logger
set_up_file_logger = utilities.set_up_file_logger


class TestUtilities:
    """Test class for utility functions"""
    
    @pytest.fixture
    def temp_home(self, tmp_path, monkeypatch):
        """Fixture to create a temporary home directory for testing"""
        # Set up a temporary home directory
        temp_home = tmp_path / "test_home"
        temp_home.mkdir()
        monkeypatch.setenv("HOME", str(temp_home))
        return temp_home
    
    @pytest.fixture
    def original_cwd(self):
        """Save and restore the current working directory"""
        original_cwd = os.getcwd()
        yield original_cwd
        os.chdir(original_cwd)
    
    def test_name_uesgraph_function(self):
        """Test name_uesgraph function"""
        # Test with a workspace name provided
        result = name_uesgraph("test_workspace")
        assert result == "test_workspace"
        
        # Test with None (should return default)
        result = name_uesgraph(None)
        assert result == "Project"
        
        # Test with no argument (should return default)
        result = name_uesgraph()
        assert result == "Project"
    
    def test_set_up_terminal_logger_basic(self):
        """Test basic terminal logger setup"""
        logger_name = "test_terminal_logger"
        logger = set_up_terminal_logger(logger_name)
        
        # Verify logger properties
        assert isinstance(logger, logging.Logger)
        assert logger.name == logger_name
        assert logger.level == logging.INFO  # Default level
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert logger.propagate == False
        
        # Clean up
        logger.handlers.clear()
    
    def test_set_up_terminal_logger_custom_level(self):
        """Test terminal logger with custom log level"""
        logger_name = "test_terminal_logger_debug"
        logger = set_up_terminal_logger(logger_name, level=logging.DEBUG)
        
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) == 1
        
        # Clean up
        logger.handlers.clear()
    
    def test_set_up_terminal_logger_duplicate_calls(self):
        """Test that duplicate calls don't add multiple handlers"""
        logger_name = "test_duplicate_logger"
        
        # First call
        logger1 = set_up_terminal_logger(logger_name)
        handler_count1 = len(logger1.handlers)
        
        # Second call with same name
        logger2 = set_up_terminal_logger(logger_name)
        handler_count2 = len(logger2.handlers)
        
        # Should be the same logger instance and same handler count
        assert logger1 is logger2
        assert handler_count1 == handler_count2 == 1
        
        # Clean up
        logger1.handlers.clear()
    
    def test_set_up_file_logger_basic(self):
        """Test basic file logger setup"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger_name = "test_file_logger"
            logger = set_up_file_logger(logger_name, log_dir=temp_dir)
            
            # Verify logger properties
            assert isinstance(logger, logging.Logger)
            assert logger.name == logger_name
            assert logger.level == logging.ERROR  # Default level
            assert len(logger.handlers) == 1
            assert isinstance(logger.handlers[0], logging.FileHandler)
            assert logger.propagate == False
            
            # Verify log file was created
            log_files = [f for f in os.listdir(temp_dir) if f.startswith(logger_name)]
            assert len(log_files) == 1
            assert log_files[0].endswith('.log')
            
            # Clean up
            logger.handlers.clear()
    
    def test_set_up_file_logger_default_temp_dir(self):
        """Test file logger with default temp directory"""
        logger_name = "test_file_logger_default"
        logger = set_up_file_logger(logger_name)
        
        # Should use system temp directory
        assert len(logger.handlers) == 1
        log_file_path = logger.handlers[0].baseFilename
        temp_dir = tempfile.gettempdir()
        assert log_file_path.startswith(temp_dir)
        
        # Verify log file exists
        assert os.path.exists(log_file_path)
        
        # Clean up
        logger.handlers.clear()
        try:
            os.remove(log_file_path)
        except OSError:
            pass  # File might already be removed
    
    def test_set_up_file_logger_custom_level(self):
        """Test file logger with custom log level"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger_name = "test_file_logger_info"
            logger = set_up_file_logger(logger_name, log_dir=temp_dir, level=logging.INFO)
            
            assert logger.level == logging.INFO
            
            # Clean up
            logger.handlers.clear()
    
    def test_logger_functionality_integration(self):
        """Integration test for logger functionality"""
        # Test that loggers actually work for logging messages
        terminal_logger = set_up_terminal_logger("integration_terminal_test")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            file_logger = set_up_file_logger("integration_file_test", log_dir=temp_dir)
            
            # Test logging (these shouldn't raise exceptions)
            terminal_logger.info("This is a test info message")
            file_logger.error("This is a test error message")
            
            # Verify file logger actually wrote to file
            log_files = [f for f in os.listdir(temp_dir) if f.startswith("integration_file_test")]
            assert len(log_files) == 1
            
            log_file_path = os.path.join(temp_dir, log_files[0])
            with open(log_file_path, 'r') as f:
                log_content = f.read()
                assert "This is a test error message" in log_content
            
            # Clean up
            terminal_logger.handlers.clear()
            file_logger.handlers.clear()