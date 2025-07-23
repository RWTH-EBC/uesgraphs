Welcome to uesgraphs documentation!
====================================

**uesgraphs** is a Python package for describing Urban Energy Systems, managing their data within a Python graph structure, and enabling the automatic generation of dynamic district simulation models.

Overview
--------

**uesgraphs** extends the `networkx <https://networkx.github.io/>`_ Graph class and adds basic methods to represent buildings and energy networks in the graph. It can be used as a foundation to:

- Analyze energy network structures
- Evaluate district energy systems  
- Generate simulation models

Features
--------

**Version 2** includes the following enhancements:

- **Simplified Installation**: Easier installation with removal of unnecessary Python library dependencies
- **Enabled Logging Features**: Logging functionality for better tracking and debugging
- **Enhanced Compatibility**: Compatible with the latest versions of Modelica and the AixLib package
- **Improved Visualization**: Enhanced visualization features for better representation of results
- **Addition of analyze.py**: Post-processing and visualization for dynamic district simulations
- **Updated Model Template Generation**: Automation of multiple models
- **Updated Examples**: New examples clarifying template generation and analyze.py usage

Quick Start
-----------

Install uesgraphs using conda:

.. code-block:: bash

   conda create -n uesgraphs python=3.13
   conda activate uesgraphs
   pip install -e .

API Documentation
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   code/modules

Main Classes
------------

.. autosummary::
   :toctree: _autosummary

   uesgraphs.UESGraph
   uesgraphs.Visuals

Modules
-------

Core Modules
~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary

   uesgraphs.uesgraph
   uesgraphs.visuals
   uesgraphs.analyze
   uesgraphs.template_generation
   uesgraphs.utilities

System Models
~~~~~~~~~~~~~

.. autosummary::
   :toctree: _autosummary

   uesgraphs.systemmodels.systemmodelheating
   uesgraphs.systemmodels.templates
   uesgraphs.systemmodels.utilities

Examples
~~~~~~~~

.. autosummary::
   :toctree: _autosummary

   uesgraphs.examples

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
