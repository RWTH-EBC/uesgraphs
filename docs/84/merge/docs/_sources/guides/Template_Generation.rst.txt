Template Generation
===============================

This guide shows how to quickly generate a Modelica template for an AixLib component using UESGraphs.

Requirements
------------

**Software:**

- **OpenModelica**: Version 1.24.x or 1.26.x recommended

  - Download from `openmodelica.org <https://openmodelica.org/download/>`_
  - Ensure OpenModelica is added to your system PATH

- **OMPython**: Version 3.x (3.4.0 to <4.0.0)

  - Install with: ``pip install "uesgraphs[templates]"``
  - OMPython 4.0.0+ is not yet supported due to breaking API changes

- **AixLib**: Local copy of the AixLib Modelica library

  - Clone from `RWTH-EBC/AixLib <https://github.com/RWTH-EBC/AixLib>`_

**Tested Configurations:**

- OpenModelica 1.24.4 + OMPython 3.6.0 ✓
- OpenModelica 1.26.0 + OMPython 3.6.0 ✓

Generating a Template (Example)
------------------------------

You can generate a template for an AixLib component with just a few lines of code:

.. code-block:: python

   from uesgraphs.systemmodels.templates import UESTemplates
   
   # Example: Generate template for StaticPipe model
   model_name = "AixLib.Fluid.DistrictHeatingCooling.Pipes.StaticPipe"
   model_type = "Pipe"
   
   template = UESTemplates(model_name=model_name, model_type=model_type)
   template.generate_new_template(path_library="path/to/AixLib/package.mo")
   print(f"Template saved at: {template.save_path}")



Bulk Template Generation
-------------------------

For generating multiple templates at once, use the ``generate_bulk()`` method:

.. code-block:: python

   from uesgraphs.systemmodels.templates import UESTemplates

   models = {
       "Pipe": [
           "AixLib.Fluid.DistrictHeatingCooling.Pipes.StaticPipe",
           "AixLib.Fluid.FixedResistances.PlugFlowPipe",
       ],
       "Demand": [
           "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
       ]
   }

   results = UESTemplates.generate_bulk(
       models,
       library_path="/path/to/AixLib/package.mo",
       workspace="./templates"
   )

For frequent use, consider an environment variable to avoid specifying the path each time:

.. code-block:: bash

   export AIXLIB_LIBRARY_PATH=/path/to/AixLib/package.mo

See also example 12: demonstrate_config_generation()

Parameter Type Support
----------------------

The template generation has been tested with standard AixLib components used in uesgraphs (pipes, demands, supplies). The following applies to these components:

**Confirmed Support:**

- **Boolean**: Explicitly converted to Modelica boolean syntax

  - Python: ``enable=True`` → Modelica: ``enable=true``
  - **Important**: Requires special handling to work correctly in Modelica code

- **Real (Float)**: Numeric parameter values

  - Values are rounded to 10 decimal places
  - All physical quantities must be in **SI units** (meters, kilograms, seconds, etc.)

- **Python Keywords**: Parameters with names that are Python keywords (e.g., ``lambda``) are detected during generation and you'll be prompted to provide an alternative name

.. warning::
   **For custom AixLib components**: The template generation is optimized for standard district heating/cooling components. If you're generating templates for other AixLib components with different parameter types (Strings, Enumerations, Records, etc.), verify the generated template works correctly before use. Manual adjustments may be necessary.

Precision & SI Units
--------------------

**Rounding**: Real values are rounded to 10 decimal places during template generation.

**Typical parameter ranges** (examples from standard district heating components):

- Pipe roughness: ~1e-6 m (micrometers) ✓
- Diameters: 0.01 - 1.0 m ✓
- Thermal conductivity: 0.001 - 10 W/(m·K) ✓

**Potential precision issues**: Values smaller than 1e-10 may be affected by rounding. If you need extreme precision for specialized applications, verify the generated parameter values.

Common Issues
-------------

**Template generation fails with "Could not load package.mo":**

- Check that OpenModelica is installed and in your PATH
- Verify the path to ``package.mo`` is correct
- Ensure you're using OMPython 3.x (not 4.0.0+)

**Parameters missing in generated template:**

- Only Boolean and Real types are supported
- Check if the parameter has a supported type in the Modelica model

**Python keyword conflicts:**

- You'll be prompted to rename parameters that conflict with Python keywords
- Choose descriptive alternatives (e.g., ``lambda_ground`` instead of ``lambda``)

Next Steps
----------

For more examples including configuration-driven generation, see :doc:`../api_examples` (Example 12).
