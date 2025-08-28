"""
AixLib Masks Management Module

This module provides flexible mask loading and management for different AixLib versions.
It supports both YAML configuration files and embedded fallback defaults.

Features:
- Hybrid loading: YAML files with embedded fallbacks
- Version-specific mask configurations
- Extensible variable definitions
- Validation and error handling
- Future-ready for component discovery

Usage:
    from uesgraphs.analysis.masks import load_aixlib_masks, get_variable_patterns
    
    # Load masks for a specific version
    masks = load_aixlib_masks("2.1.0")
    
    # Get edge variable patterns
    edge_patterns = get_variable_patterns(masks, "edge_variables")
"""

import yaml
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple


def set_up_logger() -> logging.Logger:
    """Set up a simple logger for the masks module."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


# Embedded fallback masks (minimal but functional)
DEFAULT_MASKS = {
    "2.1.0": {
        "component_discovery": {
            "enabled": False,
            "pipe_pattern": r"networkModel\.pipe(\d+)([R]?)\."
        },
        "edge_variables": {
            "mass_flow": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.port_a.m_flow",
                "unit": "kg/s",
                "description": "Mass flow rate through the pipe"
            },
            "pressure_drop": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.dp",
                "unit": "Pa",
                "description": "Pressure drop across the pipe"
            },
            "pressure_inlet": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.port_a.p",
                "unit": "Pa",
                "description": "Pressure at pipe inlet"
            },
            "pressure_outlet": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.port_b.p",
                "unit": "Pa",
                "description": "Pressure at pipe outlet"
            },
            "temperature_inlet": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.sta_a.T",
                "unit": "K",
                "description": "Temperature at pipe inlet"
            },
            "temperature_outlet": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.sta_b.T",
                "unit": "K",
                "description": "Temperature at pipe outlet"
            }
        },
        "node_variables": {
            "temperature": {
                "source_patterns": ["sta_{port}.T"],
                "unit": "K",
                "description": "Node temperature from connected pipes",
                "assignment_strategy": "consistent_value"
            },
            "pressure": {
                "source_patterns": ["port_{port}.p"],
                "unit": "Pa",
                "description": "Node pressure from connected pipes",
                "assignment_strategy": "consistent_value"
            }
        }
    },
    "2.0.0": {
        "component_discovery": {
            "enabled": False,
            "pipe_pattern": r"networkModel\.pipe(\d+)([R]?)\."
        },
        "edge_variables": {
            "mass_flow": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.port_a.m_flow",
                "unit": "kg/s",
                "description": "Mass flow rate through the pipe"
            },
            "pressure_inlet": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.port_a.p",
                "unit": "Pa",
                "description": "Pressure at pipe inlet"
            },
            "pressure_outlet": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.ports_b[1].p",
                "unit": "Pa",
                "description": "Pressure at pipe outlet"
            },
            "temperature_inlet": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.sta_a.T",
                "unit": "K",
                "description": "Temperature at pipe inlet"
            },
            "temperature_outlet": {
                "simulation_pattern": "networkModel.pipe{pipe_code}{type}.sta_b[1].T",
                "unit": "K",
                "description": "Temperature at pipe outlet"
            }
        },
        "node_variables": {
            "temperature": {
                "source_patterns": ["sta_{port}[1].T"],
                "unit": "K",
                "description": "Node temperature from connected pipes",
                "assignment_strategy": "consistent_value"
            },
            "pressure": {
                "source_patterns": ["port_{port}.p", "ports_{port}[1].p"],
                "unit": "Pa",
                "description": "Node pressure from connected pipes", 
                "assignment_strategy": "consistent_value"
            }
        }
    }
}


def load_aixlib_masks(aixlib_version: str = "2.1.0", custom_yaml_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load AixLib masks with hybrid fallback strategy.
    
    Loading priority:
    1. Custom YAML path (if provided)
    2. Package default YAML file
    3. Embedded defaults
    
    Args:
        aixlib_version: AixLib version string (e.g., "2.1.0")
        custom_yaml_path: Optional path to custom YAML configuration
        
    Returns:
        Dictionary containing mask configuration for the specified version
        
    Raises:
        ValueError: If the specified version is not supported
        FileNotFoundError: If custom_yaml_path is specified but doesn't exist
    """
    logger = set_up_logger()
    
    # Step 1: Try to load from YAML (custom or package default)
    masks_data = None
    yaml_source = None
    
    if custom_yaml_path:
        if not os.path.exists(custom_yaml_path):
            raise FileNotFoundError(f"Custom YAML path does not exist: {custom_yaml_path}")
        masks_data = _load_yaml_masks(custom_yaml_path)
        yaml_source = f"custom file: {custom_yaml_path}"
    else:
        # Try package default YAML
        package_yaml = Path(__file__).parent / "aixlib_masks.yaml"
        if package_yaml.exists():
            masks_data = _load_yaml_masks(package_yaml)
            yaml_source = f"package file: {package_yaml}"
    
    # Step 2: Use YAML data if loaded successfully
    if masks_data and aixlib_version in masks_data:
        logger.info(f"Loaded AixLib {aixlib_version} masks from {yaml_source}")
        return masks_data[aixlib_version]
    elif masks_data:
        available_versions = list(masks_data.keys())
        logger.warning(f"Version {aixlib_version} not found in YAML. Available: {available_versions}")
    
    # Step 3: Fall back to embedded defaults
    if aixlib_version in DEFAULT_MASKS:
        logger.info(f"Using embedded default masks for AixLib {aixlib_version}")
        logger.info("💡 Consider updating to YAML configuration for full feature support")
        return DEFAULT_MASKS[aixlib_version]
    
    # Step 4: Version not supported anywhere
    available_versions = list(DEFAULT_MASKS.keys())
    raise ValueError(f"AixLib version '{aixlib_version}' not supported. Available versions: {available_versions}")


def _load_yaml_masks(yaml_path: Path) -> Dict[str, Any]:
    """
    Load masks from YAML file with error handling.
    
    Args:
        yaml_path: Path to YAML file
        
    Returns:
        Loaded YAML data
        
    Raises:
        yaml.YAMLError: If YAML parsing fails
        IOError: If file cannot be read
    """
    logger = set_up_logger()
    
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            logger.debug(f"Successfully loaded YAML from {yaml_path}")
            return data
    except yaml.YAMLError as e:
        logger.error(f"YAML parsing error in {yaml_path}: {e}")
        raise
    except IOError as e:
        logger.error(f"Could not read YAML file {yaml_path}: {e}")
        raise


def get_variable_patterns(masks: Dict[str, Any], variable_type: str) -> Dict[str, str]:
    """
    Extract simulation patterns for a specific variable type.
    
    Args:
        masks: Loaded mask configuration
        variable_type: Either "edge_variables" or "node_variables"
        
    Returns:
        Dictionary mapping variable names to simulation patterns
        
    Example:
        >>> masks = load_aixlib_masks("2.1.0")
        >>> edge_patterns = get_variable_patterns(masks, "edge_variables")
        >>> print(edge_patterns["mass_flow"])
        'networkModel.pipe{pipe_code}{type}.port_a.m_flow'
    """
    if variable_type not in masks:
        raise KeyError(f"Variable type '{variable_type}' not found in masks")
    
    patterns = {}
    for var_name, config in masks[variable_type].items():
        if "simulation_pattern" in config:
            patterns[var_name] = config["simulation_pattern"]
    
    return patterns


def get_node_variable_config(masks: Dict[str, Any], variable_name: str) -> Dict[str, Any]:
    """
    Get complete configuration for a node variable.
    
    Args:
        masks: Loaded mask configuration  
        variable_name: Name of the node variable (e.g., "temperature", "pressure")
        
    Returns:
        Complete configuration dictionary for the variable
        
    Raises:
        KeyError: If variable is not found
    """
    if "node_variables" not in masks:
        raise KeyError("No node_variables configuration found in masks")
    
    if variable_name not in masks["node_variables"]:
        available_vars = list(masks["node_variables"].keys())
        raise KeyError(f"Node variable '{variable_name}' not found. Available: {available_vars}")
    
    return masks["node_variables"][variable_name].copy()


def validate_mask_structure(masks: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the structure of loaded masks.
    
    Args:
        masks: Loaded mask configuration
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required top-level keys
    required_keys = ["edge_variables", "node_variables", "component_discovery"]
    for key in required_keys:
        if key not in masks:
            issues.append(f"Missing required top-level key: {key}")
    
    # Validate edge variables
    if "edge_variables" in masks:
        for var_name, config in masks["edge_variables"].items():
            if not isinstance(config, dict):
                issues.append(f"Edge variable '{var_name}' must be a dictionary")
                continue
            
            if "simulation_pattern" not in config:
                issues.append(f"Edge variable '{var_name}' missing 'simulation_pattern'")
            
            if "unit" not in config:
                issues.append(f"Edge variable '{var_name}' missing 'unit'")
    
    # Validate node variables
    if "node_variables" in masks:
        for var_name, config in masks["node_variables"].items():
            if not isinstance(config, dict):
                issues.append(f"Node variable '{var_name}' must be a dictionary")
                continue
            
            if "source_patterns" not in config:
                issues.append(f"Node variable '{var_name}' missing 'source_patterns'")
            elif not isinstance(config["source_patterns"], list):
                issues.append(f"Node variable '{var_name}' 'source_patterns' must be a list")
            
            if "assignment_strategy" not in config:
                issues.append(f"Node variable '{var_name}' missing 'assignment_strategy'")
    
    return len(issues) == 0, issues


def list_available_versions(custom_yaml_path: Optional[str] = None) -> List[str]:
    """
    List all available AixLib versions.
    
    Args:
        custom_yaml_path: Optional path to custom YAML configuration
        
    Returns:
        List of supported version strings
    """
    versions = set()
    
    # Add embedded versions
    versions.update(DEFAULT_MASKS.keys())
    
    # Add YAML versions if available
    try:
        if custom_yaml_path and os.path.exists(custom_yaml_path):
            yaml_data = _load_yaml_masks(Path(custom_yaml_path))
            versions.update(yaml_data.keys())
        else:
            package_yaml = Path(__file__).parent / "aixlib_masks.yaml"
            if package_yaml.exists():
                yaml_data = _load_yaml_masks(package_yaml)
                versions.update(yaml_data.keys())
    except Exception:
        # If YAML loading fails, just use embedded versions
        pass
    
    return sorted(list(versions))


def get_legacy_masks(aixlib_version: str) -> Dict[str, str]:
    """
    Get legacy-style masks for backward compatibility with old analyze.py.
    
    This function provides the old format masks for existing code that hasn't
    been updated to use the new enhanced mask system.
    
    Args:
        aixlib_version: AixLib version string
        
    Returns:
        Dictionary in the old format: {"m_flow": "pattern", "dp": "pattern", ...}
    """
    masks = load_aixlib_masks(aixlib_version)
    edge_patterns = get_variable_patterns(masks, "edge_variables")
    
    # Map new names back to old names for compatibility
    legacy_mapping = {
        "m_flow": "mass_flow",
        "dp": "pressure_drop", 
        "p_a": "pressure_inlet",
        "p_b": "pressure_outlet",
        "T_a": "temperature_inlet",
        "T_b": "temperature_outlet"
    }
    
    legacy_masks = {}
    for old_name, new_name in legacy_mapping.items():
        if new_name in edge_patterns:
            legacy_masks[old_name] = edge_patterns[new_name]
    
    return legacy_masks


# Convenience function for quick access
def get_masks(aixlib_version: str = "2.1.0") -> Dict[str, str]:
    """
    Quick access to legacy-format masks for backward compatibility.
    
    This is a drop-in replacement for the old get_MASKS() function.
    """
    return get_legacy_masks(aixlib_version)


if __name__ == "__main__":
    # Demo usage
    print("🔧 AixLib Masks Demo")
    print("=" * 50)
    
    # List available versions
    versions = list_available_versions()
    print(f"Available versions: {versions}")
    
    # Load masks for 2.1.0
    masks = load_aixlib_masks("2.1.0")
    print(f"\n📋 Loaded mask configuration for AixLib 2.1.0")
    
    # Show edge variables
    edge_patterns = get_variable_patterns(masks, "edge_variables")
    print(f"\n🔗 Edge variables ({len(edge_patterns)}):")
    for var_name, pattern in edge_patterns.items():
        print(f"  {var_name}: {pattern}")
    
    # Show node variables
    print(f"\n📍 Node variables:")
    for var_name in masks["node_variables"]:
        config = get_node_variable_config(masks, var_name)
        patterns = config["source_patterns"]
        strategy = config["assignment_strategy"]
        print(f"  {var_name}: {patterns} ({strategy})")
    
    # Validate structure
    is_valid, issues = validate_mask_structure(masks)
    print(f"\n✅ Mask validation: {'PASSED' if is_valid else 'FAILED'}")
    if issues:
        for issue in issues:
            print(f"  - {issue}")
    
    # Show legacy compatibility
    legacy = get_legacy_masks("2.1.0")
    print(f"\n🔄 Legacy compatibility masks:")
    for old_name, pattern in legacy.items():
        print(f"  {old_name}: {pattern}")