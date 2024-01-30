"""Utilies: Collection of all utility functions that are useful in several classes."""

import os


def default_json_path():
    """
    Creates default output file UESgraphOutput in the user dictionary.

    Paramters
    ---------
    UESgraph_defaul_path : str
        Path, where uesgraph files will be saved.

    Returns
    -------
    path : str
        Path, where to save uesgraph files
    """

    UESgraph_default_path = os.path.expanduser("~")
    UESgraph_default_path = os.path.join(UESgraph_default_path, "UESgraphOutput")
    UESgraph_default_path = os.path.abspath(UESgraph_default_path)

    if not os.path.exists(UESgraph_default_path):
        os.mkdir(UESgraph_default_path)

    if os.path.isdir(UESgraph_default_path):
        os.chdir(UESgraph_default_path)

    path = UESgraph_default_path

    return path


def make_workspace(name_workspace=None):
    """Creates a local workspace with given name

    If no name is given, the general workspace directory will be used

    Parameters
    ----------
    name_workspace : str
        Name of the local workspace to be created

    Returns
    -------
    workspace : str
        Full path to the new workspace
    """

    this_dir = default_json_path()

    if not name_workspace:
        workspace = os.path.join(this_dir, 'Project')
    else:
        workspace = os.path.join(this_dir, name_workspace)

    if not os.path.exists(workspace):
        os.mkdir(workspace)

    return workspace


def name_uesgraph(name_workspace=None):
    """Gives the uesgraph a name

    Parameters
    ----------
    name_workspace : str
        Name of the workspace of the current uesgraph

    Returns
    -------
    name_uesgraph : str
        Name of the uesgraph according to its workspace
    """

    name_uesgraph = make_workspace.name_workspace

    return name_uesgraph
