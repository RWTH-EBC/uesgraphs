# -*- coding: utf-8 -*-
"""
Bulk Template Generation for AixLib Components
===========================================

This module provides functionality for automated bulk generation of Mako templates
for multiple AixLib components. It processes component specifications from a 
central configuration file and generates corresponding templates for use with 
UESGraphs.

Configuration:
------------
- Component specifications are read from 'uesgraphs/data/template_aixlib_components.json'
- AixLib library path can be specified via 'AIXLIB_LIBRARY_PATH' environment variable
- Templates are generated in the specified workspace directory

Features:
--------Y
- Batch processing of multiple component templates
- Automatic template generation for new AixLib versions
- Support for all component types (demands, supplies, pipes)
- Configurable rigorous mode for automated overwriting

Parameters:
----------
workspace : str
    Directory where generated templates will be stored
rigorous : bool, optional
    If True, automatically overwrites existing templates without confirmation
    If False, prompts for confirmation before overwriting (default)

Usage Example:
------------
>>> from uesgraphs import template_generation
>>> template_generation.main(workspace="./templates")
>>> # For automated overwriting:
>>> template_generation.main(rigorous=True, workspace="./templates")

Notes:
-----
- Process might take considerable time depending on number of components
- Requires AixLib installation with correct version
- Generated templates are used for automated Modelica code generation
- Useful when updating to new AixLib versions or adding new components

Author:
-------
rka-lko
"""

import uesgraphs as ug
from uesgraphs import template_generation

from uesgraphs.examples import e1_readme_example as e1

def main():
    print("*** Generating templates for multiple models (could take a lot of time) ***")
    #Standard is current system aixlib library specified with system variable "AIXLIB_LIBRARY_PATH"
    #Models are loaded from the JSON file "data/template_aixlib_components.json"
    workspace = e1.workspace_example("e13")
    template_generation.main(workspace=workspace)
    #set rigorous to True to avoid confirmation of overwriting templates:
    template_generation.main(rigorous=True,workspace=workspace)

if __name__ == "__main__":
    main()
    print("*** Done ***")