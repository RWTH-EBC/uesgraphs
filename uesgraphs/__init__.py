from uesgraphs.uesgraph import UESGraph

from uesgraphs.visuals import Visuals

import importlib.metadata
__version__ = importlib.metadata.version("uesgraphs")

#Aixlib compatibility
def _get_aixlib_version():
    """Reads the compatible AixLib version to this uesgraphs installation from pyproject.toml file."""
    try:
        import tomllib #Python 3.11+
    except ImportError:
        import tomli as tomllib # Python 3.10 and earlier

    from pathlib import Path

    try:
        path = Path(__file__).parent.parent / "pyproject.toml"
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return data["tool"]["aixlib"]["compatible_aixlib_version"]
    except (FileNotFoundError, KeyError):
        print(f"Warning: Could not read compatible AixLib version from pyproject.toml at {path}.")
        return None
    
# Set the compatible AixLib version
__compatible_aixlib_version = _get_aixlib_version()

def get_versioning_info():
    """Returns the versioning information of uesgraphs."""
    return {
        "uesgraphs_version": __version__,
        "compatible_aixlib_version": __compatible_aixlib_version
    }