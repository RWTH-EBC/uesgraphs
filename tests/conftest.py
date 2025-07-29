import os
import matplotlib
import pytest

# Configure matplotlib for CI environments
if os.environ.get('CI') or os.environ.get('GITHUB_ACTIONS'):
    matplotlib.use('Agg')  # Use non-GUI backend

def pytest_configure(config):
    """Configure pytest for different environments."""
    # Add matplotlib marker only if pytest-mpl is available
    try:
        import pytest_mpl
        config.addinivalue_line("markers", "mpl: matplotlib comparison tests")
    except ImportError:
        # If pytest-mpl is not available, skip mpl tests
        config.addinivalue_line("markers", "mpl: matplotlib tests (skipped - pytest-mpl not available)")

def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle matplotlib tests."""
    try:
        import pytest_mpl
        mpl_available = True
    except ImportError:
        mpl_available = False
    
    if not mpl_available:
        skip_mpl = pytest.mark.skip(reason="pytest-mpl not available")
        for item in items:
            if "mpl" in item.keywords:
                item.add_marker(skip_mpl)