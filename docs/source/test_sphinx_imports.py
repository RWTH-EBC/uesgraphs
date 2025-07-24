#!/usr/bin/env python3
"""
Test script to verify that uesgraphs modules can be imported for documentation generation.
This simulates what Sphinx would do during autodoc.
"""

import sys
import os

# Add the uesgraphs package to Python path (same as in conf.py)
sys.path.insert(0, os.path.abspath('../../'))

def test_imports():
    """Test if all main modules can be imported."""
    print("Testing module imports for Sphinx documentation...")
    
    try:
        # Test main package import
        import uesgraphs
        print("✓ uesgraphs package imported successfully")
        
        # Test main classes
        from uesgraphs import UESGraph
        print("✓ UESGraph class imported successfully")
        
        from uesgraphs import Visuals
        print("✓ Visuals class imported successfully")
        
        # Test individual modules
        import uesgraphs.uesgraph
        print("✓ uesgraphs.uesgraph module imported successfully")
        
        import uesgraphs.visuals
        print("✓ uesgraphs.visuals module imported successfully")
        
        # Test if other modules exist
        try:
            import uesgraphs.analyze
            print("✓ uesgraphs.analyze module imported successfully")
        except ImportError as e:
            print(f"⚠ uesgraphs.analyze not found: {e}")
        
        try:
            import uesgraphs.template_generation
            print("✓ uesgraphs.template_generation module imported successfully")
        except ImportError as e:
            print(f"⚠ uesgraphs.template_generation not found: {e}")
        
        try:
            import uesgraphs.utilities
            print("✓ uesgraphs.utilities module imported successfully")
        except ImportError as e:
            print(f"⚠ uesgraphs.utilities not found: {e}")
        
        # Test systemmodels
        try:
            import uesgraphs.systemmodels.systemmodelheating
            print("✓ uesgraphs.systemmodels.systemmodelheating imported successfully")
        except ImportError as e:
            print(f"⚠ uesgraphs.systemmodels.systemmodelheating not found: {e}")
        
        try:
            import uesgraphs.examples
            print("✓ uesgraphs.examples imported successfully")
        except ImportError as e:
            print(f"⚠ uesgraphs.examples not found: {e}")
        
        print("\n✅ Basic import test completed successfully!")
        print("The modules should work with Sphinx autodoc.")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_docstrings():
    """Test if classes have docstrings for documentation."""
    print("\nTesting docstrings...")
    
    try:
        from uesgraphs import UESGraph, Visuals
        
        if UESGraph.__doc__:
            print("✓ UESGraph has docstring")
        else:
            print("⚠ UESGraph missing docstring")
        
        if Visuals.__doc__:
            print("✓ Visuals has docstring")
        else:
            print("⚠ Visuals missing docstring")
            
    except Exception as e:
        print(f"❌ Docstring test failed: {e}")

if __name__ == "__main__":
    success = test_imports()
    test_docstrings()
    
    if success:
        print("\n🎉 Your uesgraphs package should work fine with Sphinx documentation!")
    else:
        print("\n❌ There are import issues that need to be fixed before Sphinx can generate documentation.")
