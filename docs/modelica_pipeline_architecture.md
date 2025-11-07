# UESGraphs Modelica Code Generation Pipeline
## Architecture Documentation

**Version:** 2.1
**Last Updated:** November 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Pipeline Architecture](#pipeline-architecture)
3. [Component Interaction](#component-interaction)
4. [Excel-Template System](#excel-template-system)
5. [Parameter Assignment Flow](#parameter-assignment-flow)
6. [Connector Handling](#connector-handling)
7. [Validation System](#validation-system)
8. [Code Generation Process](#code-generation-process)
9. [Extension Guide](#extension-guide)

---

## Overview

The UESGraphs Modelica code generation pipeline converts district heating network graphs into executable Modelica simulation models. The pipeline uses an Excel-based configuration system that integrates with Mako templates to generate component-specific Modelica code.

### Key Design Principles

1. **Separation of Concerns**: Network topology (graph), parameters (Excel), and code structure (templates) are separated
2. **Convention over Configuration**: Standardized naming conventions reduce explicit configuration
3. **Validation by Design**: Templates define their own requirements via introspection
4. **Flexible Parameter Sources**: Support for graph attributes, Excel values, and cross-references

### Technology Stack

- **Graph Representation**: NetworkX-based UESGraph
- **Configuration**: Excel (openpyxl)
- **Templates**: Mako templating engine
- **Target Language**: Modelica (AixLib components)

---

## Pipeline Architecture

### High-Level Flow

```
GeoJSON/Graph Input
        ↓
   UESGraph Creation
        ↓
┌───────────────────────┐
│  uesgraph_to_modelica │ ← Main Entry Point
└───────────────────────┘
        ↓
   ┌─────────────────────────────┐
   │ 1. Validate Input Files     │
   │ 2. Load Excel Configuration │
   │ 3. Assign Demand Data       │
   │ 4. Assign Pipe Parameters   │
   │ 5. Assign Supply Parameters │
   │ 6. Assign Demand Parameters │
   │ 7. Generate Modelica Code   │
   └─────────────────────────────┘
        ↓
   Modelica .mo Files
```

### Core Components

#### 1. Main Pipeline Function (`uesgraph_to_modelica`)
- **Location**: `systemmodels/model_generation_pipeline.py`
- **Responsibility**: Orchestrate the complete workflow
- **Input**: UESGraph or JSON path, Excel config, demand CSVs, ground temperature data
- **Output**: Timestamped directory with Modelica files

#### 2. Parameter Assignment Functions
- `assign_pipe_parameters()`: Configure pipe network
- `assign_supply_parameters()`: Configure supply stations
- `assign_demand_parameters()`: Configure demand substations

#### 3. Template System
- **Location**: `systemmodels/templates.py` (UESTemplates class)
- **Templates**: `data/templates/network/{pipe,supply,demand}/*.mako`
- **Responsibility**: Define component structure and parameters

#### 4. Code Generation
- **Location**: `systemmodels/systemmodelheating.py` (SystemModelHeating class)
- **Responsibility**: Render templates and write Modelica files

---

## Component Interaction

### Data Flow Diagram

```
                         ┌─────────────────┐
                         │  Excel Config   │
                         │  (.xlsx)        │
                         └────────┬────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ↓                           ↓
         ┌──────────────────┐        ┌─────────────────┐
         │   Simulation     │        │  Component      │
         │   Settings       │        │  Parameters     │
         │   (Sheet 1)      │        │  (Sheets 2-4)   │
         └──────────┬───────┘        └────────┬────────┘
                    │                         │
                    └──────────┬──────────────┘
                               ↓
                    ┌──────────────────────┐
                    │  parse_template_     │
                    │  parameters()        │
                    │  - Reads .mako       │
                    │  - Extracts MAIN/AUX │
                    │  - Extracts connectors│
                    └──────────┬───────────┘
                               ↓
┌─────────────┐     ┌──────────────────────┐     ┌──────────────┐
│  UESGraph   │────→│  assign_*_parameters │────→│  UESGraph    │
│  (input)    │     │  - Validate MAIN     │     │  (enriched)  │
│             │     │  - Assign from Excel │     │              │
│  - Topology │     │  - Resolve @refs     │     │  + Parameters│
│  - Geometry │     │  - Process connectors│     │  + Connectors│
└─────────────┘     └──────────────────────┘     └──────┬───────┘
                                                          │
                                                          ↓
                                                  ┌───────────────┐
                                                  │  Template     │
                                                  │  Rendering    │
                                                  │  (.mako)      │
                                                  └───────┬───────┘
                                                          │
                                                          ↓
                                                  ┌───────────────┐
                                                  │  Modelica     │
                                                  │  Code (.mo)   │
                                                  └───────────────┘
```

---

## Excel-Template System

### Design Philosophy

The Excel-Template system provides a **declarative** approach to parameter configuration:

1. **Templates Define Requirements**: Templates specify their own parameter needs
2. **Excel Provides Values**: Excel sheets provide uniform values for component types
3. **Graph Preserves Specifics**: Graph attributes override Excel for component-specific values

### Template Parameter Declaration

Templates use **Python-executable defs** to declare their parameters:

```mako
<%def name="get_main_parameters()">
   Q_flow_nominal dTDesign TReturn dTBuilding TSupplyBuilding
</%def>

<%def name="get_aux_parameters()">
   cp_default dp_nominal deltaM tau allowFlowReversal
</%def>

<%def name="get_connector_names()">
   Q_flow_input
</%def>
```

**Categories:**
- **MAIN**: Required parameters (pipeline fails if missing)
- **AUX**: Optional parameters (Modelica defaults used if missing)
- **Connectors**: Input variables requiring time-series data

### Excel Sheet Structure

Each component type has a dedicated sheet:

| Sheet | Component Type | Purpose |
|-------|---------------|---------|
| Simulation | System-wide | Solver, time settings, medium |
| Pipes | Edges | Insulation, roughness, diameter refs |
| Supply | Supply nodes | Max demand, pressures, temperatures |
| Demands | Demand nodes | Heat exchanger settings, temperatures |

**Excel Format:**
```
Parameter         | Value                    | Unit      | Templates | Description
------------------|--------------------------|-----------|-----------|-------------
template          | AixLib_Fluid_...         | -         |           | Template name
dp_nominal        | 0.1                      | bar       |           | Nominal pressure drop
diameter          | @diameter                | m         |           | Reference to graph attr
```

### Reference System (@-notation)

Excel values starting with `@` reference graph attributes:

```python
# Excel: diameter = "@diameter"
# For edge (n1, n2) with graph.edges[n1, n2]['diameter'] = 0.15:
#   → Resolves to 0.15

# Excel: TSupply = "@T_heat_supply"
# For node 'bldg1' with graph.nodes['bldg1']['T_heat_supply'] = 343.15:
#   → Resolves to 343.15
```

**Benefits:**
- Component-specific values from GeoJSON
- Type safety (values must exist)
- Traceability (explicit data flow)

---

## Parameter Assignment Flow

### Execution Order

```
1. Load Excel sheet for component type
   ↓
2. Parse template to get MAIN/AUX/CONNECTOR lists
   ↓
3. For each component (node/edge):
   ├─ Check MAIN parameters:
   │  ├─ In graph? → Keep (don't overwrite)
   │  ├─ In Excel? → Resolve and assign
   │  └─ Missing? → ERROR
   │
   ├─ Check AUX parameters:
   │  ├─ In graph? → Keep
   │  ├─ In Excel? → Resolve and assign
   │  └─ Missing? → WARNING (use Modelica default)
   │
   └─ Check CONNECTORS:
      ├─ In graph? → Keep or convert to time-series
      ├─ In Excel? → Resolve and convert
      └─ Missing? → INFO (connector optional)
```

### Priority Rules

**Parameter Priority (highest to lowest):**
1. **Graph attributes** (from GeoJSON or programmatically set)
2. **Excel template values** (uniform across component type)
3. **Modelica defaults** (for AUX parameters only)

**Example:**
```python
# Excel: dp_nominal = 0.1
# Graph edge: graph.edges[e1, e2]['dp_nominal'] = 0.05

# Result: dp_nominal = 0.05  ← Graph wins
```

### Resolution Process

```python
def resolve_parameter_value(excel_value, component_data, param_name, component_id):
    """
    Resolve Excel value to actual parameter value.

    Cases:
    1. Direct value (number/string): Use as-is
    2. @reference: Look up in component_data
    3. Missing attribute: Raise ValueError
    """
    if not isinstance(excel_value, str):
        return excel_value  # Direct value

    if excel_value.startswith('@'):
        attr_name = excel_value[1:]  # Remove @
        if attr_name not in component_data:
            raise ValueError(f"Attribute '{attr_name}' not found in {component_id}")
        return component_data[attr_name]

    return excel_value  # String value
```

---

## Connector Handling

### Purpose

Connectors represent **dynamic inputs** to Modelica components (e.g., demand profiles, supply temperatures). They require **time-series data** rather than scalar values.

### Declaration

Templates declare connectors via `get_connector_names()`:

```mako
## demand/HeatPumpCarnot.mako
<%def name="get_connector_names()">
   Q_flow_input
</%def>

## Template usage:
Modelica.Blocks.Interfaces.RealInput ${str(name + 'Q_flow_input')}
```

### Convention: Demand Data Mapping

For demand substations, a **naming convention** links CSV data to connectors:

| Graph Attribute | Connector Variable | Meaning |
|-----------------|-------------------|---------|
| `input_heat` | `Q_flow_input` | Heating demand profile |
| `input_cool` | `Q_flow_cool` | Cooling demand profile |
| `input_dhw` | `Q_flow_dhw` | DHW demand profile |

**Pipeline behavior:**
1. User provides demand CSVs (heating, cooling, DHW)
2. Pipeline assigns to `input_heat`, `input_cool`, `input_dhw` graph attributes
3. If template has `Q_flow_input` connector:
   - Pipeline looks for `input_heat` attribute
   - Converts to time-series format
   - Saves as CSV resource file
   - Links in Modelica code

### Time-Series Conversion

```python
def _process_component_connectors(component_data, connector_params, time_array):
    """
    Convert connector data to time-series format.

    Input: connector_data = [v1, v2, ..., vn]  (Python list)
    Output: [[t1, v1], [t2, v2], ..., [tn, vn]]  (time-series)
    """
    for connector_name in connector_params:
        attr_name = excel_params.get(connector_name)  # e.g., "@input_heat"

        if attr_name.startswith('@'):
            data = component_data[attr_name[1:]]  # Get list from graph

            if isinstance(data, list):
                # Convert to time-series
                time_series = [[t, v] for t, v in zip(time_array, data)]
                component_data[connector_name] = time_series
```

---

## Validation System

### Multi-Level Validation

#### 1. File Validation
- **When**: Pipeline start
- **What**: Check existence of Excel, CSVs, GeoJSON
- **Failure**: Immediate error

#### 2. Template Parsing
- **When**: Before parameter assignment
- **What**: Parse template to extract MAIN/AUX/CONNECTOR lists
- **Failure**: Template syntax error

#### 3. Parameter Validation
- **When**: During parameter assignment
- **What**:
  - MAIN parameters: Error if missing
  - AUX parameters: Warning if missing
  - @references: Error if attribute doesn't exist
- **Failure**:
  - MAIN missing → Error, stop pipeline
  - AUX missing → Warning, continue (use Modelica default)
  - Bad reference → Error, stop pipeline

#### 4. Connector Validation
- **When**: During connector processing
- **What**: Check if connector data is available
- **Failure**: Info message (connectors optional unless required by template logic)

### Validation Reports

After each component type, the pipeline reports:

```
Processing 15 pipe(s)...
  Parameters: 45 from graph, 30 from Excel
  Connectors: 2 found
  Missing AUX: roughness, energyDynamics (will use Modelica defaults)

Processing 3 demand node(s)...
  Parameters: 12 from graph, 18 from Excel
  Connectors: 3 found
  Missing MAIN: Q_flow_nominal for node 'bldg3'
  ❌ ERROR: Required parameters missing
```

---

## Code Generation Process

### Template Rendering

The `UESTemplates` class renders Mako templates with component data:

```python
class UESTemplates:
    def render(self, node_data, **kwargs):
        """
        Render template with component-specific data.

        Args:
            node_data: Dictionary with all component attributes
            **kwargs: Additional template variables (i, number_of_instances, etc.)
        """
        # Mako templates have access to:
        # - All node_data keys as variables (e.g., ${dp_nominal})
        # - Additional kwargs (e.g., ${i} for instance index)
        # - Python code blocks for conditional logic

        return self.template.render_unicode(**node_data, **kwargs)
```

### File Organization

Generated Modelica models follow this structure:

```
workspace/
  └── e16/
      └── models/
          └── Sim20250115_143022_MySimulation/
              ├── Sim20250115_143022_MySimulation.mo    # Main model
              ├── package.mo                             # Package definition
              ├── package.order                          # Load order
              └── Resources/
                  └── Inputs/
                      ├── bldg1_input_heat.csv           # Demand profiles
                      ├── bldg2_input_heat.csv
                      └── ground_temperature.csv
```

### Code Structure

**Main model contains:**
1. **Medium packages**: Fluid property definitions
2. **Component declarations**: Pipes, supplies, demands
3. **Connector declarations**: RealInput for time-series
4. **Connections**: Fluid ports between components
5. **Ground model**: Temperature boundary condition

**Component rendering flow:**
```python
# For each demand node:
demand_template = UESTemplates(model_name="HeatPumpCarnot", model_type="Demand")
mo_code = demand_template.render(
    node_data=graph.nodes[node],  # Contains all parameters + connectors
    i=index,                        # Instance number
    number_of_instances=total       # Total count (for positioning)
)
```

---

## Extension Guide

### Adding a New Component Template

1. **Create Template File**
   ```
   uesgraphs/data/templates/network/demand/
       MyNewComponent.mako
   ```

2. **Define Parameters**
   ```mako
   <%def name="get_main_parameters()">
      param1 param2 param3
   </%def>

   <%def name="get_aux_parameters()">
      optionalParam1 optionalParam2
   </%def>

   <%def name="get_connector_names()">
      myInput
   </%def>
   ```

3. **Write Template Body**
   ```mako
   AixLib.MyLibrary.MyComponent component${name}(
     %if param1 is not None:
     param1 = ${param1},
     %endif
     param2 = ${param2},
     param3 = ${param3}
   );

   Modelica.Blocks.Interfaces.RealInput ${name}myInput;
   ```

4. **Update Excel**
   - Add row in Demands sheet: `template = MyNewComponent`
   - Add rows for param1, param2, param3 with values

5. **Test**
   ```python
   uesgraph_to_modelica(
       uesgraph=graph,
       sim_setup_path="my_config.xlsx",
       ...
   )
   ```

### Adding a New Excel Parameter

1. **Add to Template** (if required by new Modelica component version)
   ```mako
   <%def name="get_aux_parameters()">
      existingParam newParam
   </%def>

   %if newParam is not None:
   newParam = ${newParam},
   %endif
   ```

2. **Add to Excel**
   | Parameter | Value | Unit | Templates | Description |
   |-----------|-------|------|-----------|-------------|
   | newParam  | 1.5   | -    |           | New parameter description |

3. **Optional: Add Graph Attribute** (if component-specific)
   ```python
   graph.nodes['bldg1']['newParam'] = 2.0  # Override Excel value
   ```

### Custom Validation Logic

To add custom validation beyond MAIN/AUX:

```python
def assign_demand_parameters(uesgraph, excel_path, logger=None):
    # ... existing code ...

    # After standard validation, add custom checks:
    for node in demand_nodes:
        node_data = uesgraph.nodes[node]

        # Example: Validate temperature range
        if 'TSupply' in node_data and node_data['TSupply'] > 400:
            raise ValueError(f"TSupply too high for node {node}: {node_data['TSupply']} K")

        # Example: Validate parameter relationships
        if node_data.get('dTDesign', 0) > node_data.get('dTNetwork', 0):
            logger.warning(f"dTDesign > dTNetwork for node {node}, may cause issues")
```

---

## Best Practices

### For Users

1. **Start with Template Inspection**: Read the .mako files to understand parameter requirements
2. **Use @references**: Prefer `@diameter` over hardcoded values for component-specific parameters
3. **Test Incrementally**: Generate model after each configuration change
4. **Check Logs**: Set `log_level=logging.DEBUG` for detailed diagnostics

### For Developers

1. **Keep Templates Simple**: Complex logic belongs in Python, not Mako
2. **Document Parameters**: Add comments in templates explaining physical meaning
3. **Use Type Hints**: Help users understand expected parameter types
4. **Validate Early**: Check parameter validity before template rendering
5. **Provide Clear Errors**: Include component ID and parameter name in error messages

---

## Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "Required MAIN parameter missing" | Excel doesn't have parameter | Add to Excel or set as graph attribute |
| "Attribute not found" for @reference | Graph doesn't have attribute | Check GeoJSON import or set programmatically |
| Connector not linked | Wrong attribute name | Use convention: `input_heat` → `Q_flow_input` |
| Template not found | Wrong template name in Excel | Check template filename (without .mako) |
| Type error in generated model | Boolean rendered as integer | Check template rendering logic (`str().lower()`) |

### Debug Workflow

1. **Enable debug logging**
   ```python
   uesgraph_to_modelica(..., log_level=logging.DEBUG)
   ```

2. **Inspect graph after assignment**
   ```python
   assign_demand_parameters(graph, excel_path)
   print(graph.nodes['bldg1'])  # Check assigned parameters
   ```

3. **Check template parsing**
   ```python
   main, aux, conn = parse_template_parameters('Demand', 'HeatPumpCarnot')
   print(f"MAIN: {main}")
   print(f"AUX: {aux}")
   print(f"CONN: {conn}")
   ```

4. **Validate Excel structure**
   ```python
   df = pd.read_excel('config.xlsx', sheet_name='Demands')
   print(df[['Parameter', 'Value']].head(20))
   ```

---

## Migration from Old Pipeline

The old YAML-based pipeline used a different approach:

**Old (deprecated):**
- YAML configuration file
- Hardcoded parameter names in `setup_*_parameters()` functions
- Manual validation logic

**New (current):**
- Excel configuration
- Template-defined parameters (introspection)
- Automatic validation based on MAIN/AUX categories

**Migration steps:**
1. Convert YAML to Excel format (see `uesgraphs_parameters_template.xlsx`)
2. Update templates to include `get_main_parameters()` and `get_aux_parameters()`
3. Replace `generate_simulation_model()` calls with `uesgraph_to_modelica()`
4. Remove deprecated functions (`setup_building_parameters`, `setup_pipe_parameters`)

---

## Future Enhancements

Planned improvements:

1. **Schema Validation**: JSON schema for Excel structure validation
2. **Parameter Units**: Automatic unit conversion (bar → Pa)
3. **Template Inheritance**: Base templates for common parameter sets
4. **Visualization**: Parameter coverage reports (which components have which parameters)
5. **Testing**: Automated template validation suite

---

## References

- **Modelica Language**: https://modelica.org/documents/ModelicaSpec34.pdf
- **AixLib Library**: https://github.com/RWTH-EBC/AixLib
- **Mako Templates**: https://docs.makotemplates.org/
- **NetworkX**: https://networkx.org/documentation/stable/

---

*This document describes the architecture of UESGraphs version 2.1. For version-specific changes, see CHANGELOG.md.*
