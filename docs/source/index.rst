.. image:: _static/EBC_Logo.png
   :alt: EBC Logo
   :align: right



|UESgraphs|: Automated graph-based simulation model generation and analysis tool
=================================================================================

.. |UESgraphs| replace:: **UESgraphs**

.. badges-start

.. image:: https://github.com/RWTH-EBC/uesgraphs/actions/workflows/ci.yml/badge.svg?branch=master
   :target: https://github.com/RWTH-EBC/uesgraphs/actions/workflows/ci.yml
   :alt: CI Tests

.. image:: http://img.shields.io/:license-mit-blue.svg
   :target: http://doge.mit-license.org
   :alt: License: MIT
.. badges-end

**UESgraphs** (Urban Energy Systems graphs) is an open-source Python framework designed for the automated generation, simulation, and analysis of complex urban energy systems, with a focus on district heating and cooling networks. Built on a graph-based data structure, UESgraphs simplifies the challenging task of modeling interconnected energy infrastructure, enabling researchers and practitioners to rapidly create robust, dynamic simulation models ready for advanced analysis.
The tool seamlessly integrates diverse data sources, including spatial (OpenStreetMap) and tabular datasets, to build high-fidelity system graphs representing buildings, energy networks, and supply stations. Automated workflows encompass hydronic sizing, network topology optimization, and model export to simulation environments like Modelica/Dymola.

Beyond model creation, **UESgraphs** offers comprehensive post-simulation analytics and intuitive visualization capabilities, empowering users to extract actionable insights through color-coded network plots, KPIs, and interactive exploration of complex energy systems.


Getting Started
=================

The best way to start is by installing the package and checking out the :doc:`examples`.

Follow these steps to install **UESgraphs** using Conda:

1. **Create a new virtual environment**:

   .. code-block:: bash

      conda create -n uesgraphs python=3.13

   .. note::
      Replace ``3.13`` with your desired version of Python.

2. **Activate the virtual environment**:

   .. code-block:: bash

      conda activate uesgraphs

3. **Install UESgraphs from PyPI** (Quick Installation):

   If you want to use UESgraphs without modifying the source code, install directly from PyPI:

   **Basic Installation** (core functionality only):

   .. code-block:: bash

      pip install uesgraphs

   **Installation with Optional Dependencies**:

   * **For template generation and Modelica support**:

     .. code-block:: bash

        pip install uesgraphs[templates]

   * **For pandapipes simulations**:

       .. code-block:: bash
   
         pip install uesgraphs[pandapipes]

   * **For development (includes testing and coverage tools)**:

     .. code-block:: bash

        pip install uesgraphs[dev]

   * **Complete installation with all dependencies**:

     .. code-block:: bash

        pip install uesgraphs[full]

   .. note::
      If you're installing from PyPI, skip steps 4 and 5 and proceed directly to step 6 for verification, or step 7 for OpenModelica setup.

4. **Clone or download the UESgraphs repository** (Development Installation):

   If you want to modify the source code or contribute to development:

   * If you're cloning the repository using Git, run:

     .. code-block:: bash

        git clone https://github.com/RWTH-EBC/uesgraphs.git

   * If you've downloaded the repository as a ZIP file, extract it to your desired location.

5. **Install UESgraphs in editable mode** (Development Installation):

   Navigate to the directory where *UESgraphs* is located and choose your installation method:

   **Basic Installation** (core functionality only):

   .. code-block:: bash

      pip install -e <path/to/your/uesgraphs>

   **Installation with Optional Dependencies**:

   * **For template generation and Modelica support**:

     .. code-block:: bash

        pip install -e <path/to/your/uesgraphs>[templates]

   * **For pandapipes simulations**:

       .. code-block:: bash
   
         pip install -e <path/to/your/uesgraphs>[pandapipes]

   * **For development (includes testing and coverage tools)**:

     .. code-block:: bash

        pip install -e <path/to/your/uesgraphs>[dev]

   * **Complete installation with all dependencies**:

     .. code-block:: bash

        pip install -e <path/to/your/uesgraphs>[full]

   .. note::
      The ``[full]`` option installs all optional dependencies including OMPython, pytest, coverage, and other development tools. Use this for a complete development environment.

6. **Verify your UESgraphs installation** by running the automated tests:

   Navigate to the top-level *UESgraphs* folder and execute:

   .. code-block:: bash

      pytest --mpl

   This will run the test suite and verify that everything is set up correctly.

   .. note::
      Running tests requires the ``[dev]`` or ``[full]`` optional dependencies to be installed. If you only installed the basic version, install the dev dependencies first: ``pip install uesgraphs[dev]`` or ``pip install -e .[dev]`` (for editable installs).

For more detailed information, please check the ``pyproject.toml`` file.

7. **Install OpenModelica and OMPython to Run Examples 9 to 14**

   To run examples 9 to 14, you need to install **OpenModelica** and **OMPython**.

   * **Download and Install OpenModelica**:

     * Visit the `OpenModelica download page <https://openmodelica.org/download/download-windows/>`_ to download the installer for your operating system.
     * Follow the on-screen instructions to install OpenModelica on your computer.
     * Add OpenModelica to the environment variable

   * **Install OMPython**:

     If you haven't already installed OMPython with the ``[templates]`` or ``[full]`` options in step 3 or 5, you can install it separately:

     .. code-block:: bash

        pip install "OMPython>=3.4.0,<4.0.0"

     **Alternative**: If you skipped the optional dependencies, you can add them:

     For PyPI installation:

     .. code-block:: bash

        pip install uesgraphs[templates]
        # or for complete installation:
        pip install uesgraphs[full]

     For editable/development installation:

     .. code-block:: bash

        pip install -e <path/to/your/uesgraphs>[templates]
        # or for complete installation:
        pip install -e <path/to/your/uesgraphs>[full]

     **Important Notes**:

     * ✓ UESgraphs is compatible with **OMPython 3.x only** (versions ``>=3.4.0,<4.0.0``)
     * ✗ OMPython 4.0.0+ introduces breaking API changes and is **not yet supported**
     * If you encounter the error ``'OMCSessionZMQ' object has no attribute 'loadFile'``, downgrade OMPython:

       .. code-block:: bash

          pip install "OMPython==3.6.0"

     **Tested Configurations**:

     * ✓ OpenModelica 1.24.4 + OMPython 3.6.0
     * ✓ OpenModelica 1.26.0 + OMPython 3.6.0

     For more information on OMPython, refer to the `OMPython documentation <https://openmodelica.org/doc/OpenModelicaUsersGuide/latest/ompython.html#ompython>`_.


### Functional Principle
-------------------------

**UESgraphs** is built with `networkx` as its core library. The typical workflow for the tool involves:

.. image:: _static/uesgraph_function_principle.png
   :alt: Developed workflow using UESgraphs v 2.0.0
   :align: center
   :width: 100%

The functional principle of **UESgraphs** can be summarized as under:

* UESgraphs uses a graph-based structure to represent urban energy systems, where nodes denote buildings, network junctions, and supply units, and edges represent thermal and hydraulic connections like pipes.

* The core graph functionality builds on the Python NetworkX library, allowing flexible and scalable handling of complex system topologies.

* The framework supports automated preprocessing steps such as network cleaning, topology simplification, and hydronic pipe sizing to prepare accurate system models.

* Multiple data input formats are supported, including OpenStreetMap, GIS files, and manual data, enabling integration of heterogeneous spatial and tabular data.

* UESgraphs automates the generation of dynamic simulation models by transforming graph representations into Modelica code through templated model export.

* UESgraphs allows the execution of pandapipes simulations based on the graph structure and the provided input data.

* The tool facilitates downstream analysis and visualization, including color-coded plots and KPI extraction, to support evaluation and decision-making.


API Documentation
=================

  .. toctree::
     :maxdepth: 2
     :caption: User Guides:

     guides/model_generation_pipeline
     guides/hydronic_sizing
     guides/Template_Generation.rst
     guides/model_generation_pandapipes

  .. toctree::
     :maxdepth: 2
     :caption: Architecture:
     
     architecture/modelica_pipeline
     architecture/graph_transformation
     architecture/pandapipes_pipeline

  .. toctree::
     :maxdepth: 2
     :caption: API Reference:

     api_core_modules
     api_system_models
     api_system_models_pp
     api_examples

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
