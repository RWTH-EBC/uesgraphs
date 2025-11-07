# Excel-Based Model Generation Pipeline Guide

## Overview

The new Excel-based pipeline provides a unified, streamlined approach to generating Modelica simulation models from UESGraph district heating networks. All configuration is centralized in a single Excel file (`uesgraphs_parameters_template.xlsx`), making it easy to configure and manage simulation parameters, component properties, and time-series inputs.

**Key improvements over the old system:**
- ✅ Single Excel file for all configuration
- ✅ Automatic handling of connectors (time-series inputs)
- ✅ Intelligent type conversion (scientific notation, booleans)
- ✅ Clear parameter priorities (graph → Excel → defaults)
- ✅ Better validation with helpful error messages
- ✅ Support for @references to link parameters

---

## Table of Contents

1. [Pipeline Architecture](#pipeline-architecture)
2. [Excel Configuration Structure](#excel-configuration-structure)
3. [Parameter Types and Priorities](#parameter-types-and-priorities)
4. [Type Conversion](#type-conversion)
5. [Connector Handling](#connector-handling)
6. [Using @References](#using-references)
7. [Complete Workflow Example](#complete-workflow-example)
8. [Troubleshooting](#troubleshooting)
9. [Migration from Old Pipeline](#migration-from-old-pipeline)

---

## Pipeline Architecture

### High-Level Flow

```
GeoJSON Files → UESGraph → Parameter Assignment → Modelica Generation
                    ↓
              Excel Config
        (uesgraphs_parameters_template.xlsx)
```

### Processing Steps

The pipeline executes the following steps in order:

1. **Load simulation settings** from Excel 'Simulation' sheet
2. **Import or load UESGraph** from GeoJSON or JSON file
3. **Write simulation parameters to graph** (stop_time, timestep)
4. **Generate edge names** if missing (required for Modelica)
5. **Assign demand data** from CSV files to building nodes
6. **Assign pipe parameters** from Excel 'Pipes' sheet
7. **Assign supply parameters** from Excel 'Supply' sheet
8. **Assign demand parameters** from Excel 'Demands' sheet
9. **Validate all parameters** (MAIN required, AUX optional, CONNECTORS required)
10. **Generate Modelica code** using templates

Each parameter assignment step processes three categories:
- **MAIN parameters**: Required static parameters (e.g., pReturn, TReturn)
- **AUX parameters**: Optional static parameters (e.g., allowFlowReversal)
- **CONNECTORS**: Required time-series inputs (e.g., TIn, dpIn)

---

## Excel Configuration Structure

The Excel configuration file has **four sheets**:

### 1. Simulation Sheet

Defines simulation-level settings.

| Parameter | Value | Unit | Description |
|-----------|-------|------|-------------|
| simulation_name | MyProject | - | Name of the simulation |
| solver | Cvode | - | Solver algorithm |
| start_time | 0 | s | Simulation start time |
| stop_time | 86400 | s | Simulation end time (1 day) |
| timestep | 900 | s | Time step for connectors (15 min) |
| tolerance | 1e-6 | - | Solver tolerance |
| medium | AixLib.Media.Water | - | Modelica medium package |
| ground_depth | 1.0 m | - | Ground temperature depth |
| save_params_to_csv | TRUE | bool | Save parameters to CSV |

**Required parameters**: simulation_name, solver, start_time, stop_time, tolerance, medium

### 2. Pipes Sheet

Defines pipe network parameters.

| Parameter | Value | Unit | Templates | Description |
|-----------|-------|------|-----------|-------------|
| template | PlugFlowPipeEmbedded | - | - | Template name (without prefix) |
| length | @length | m | All | Use @reference to edge attribute |
| diameter | 0.15 | m | All | Pipe diameter |
| lambda_isolation | 0.024 | W/(m·K) | Embedded | Insulation thermal conductivity |
| s_isolation | 0.01 | m | Embedded | Insulation thickness |

### 3. Supply Sheet

Defines supply station parameters.

| Parameter | Value | Unit | Templates | Description |
|-----------|-------|------|-----------|-------------|
| template | SourceIdeal | - | - | Template name (shortened) |
| pReturn | 1e5 | Pa | SourceIdeal | Return pressure (MAIN) |
| TReturn | 313.15 | K | SourceIdeal | Return temperature (MAIN) |
| TIn | 353.15 | K | SourceIdeal | Supply temperature (CONNECTOR) |
| dpIn | 100000 | Pa | SourceIdeal | Pressure difference (CONNECTOR) |
| allowFlowReversal | TRUE | bool | SourceIdeal | Allow reverse flow (AUX) |

### 4. Demands Sheet

Defines demand substation parameters.

| Parameter | Value | Unit | Templates | Description |
|-----------|-------|------|-----------|-------------|
| template | HeatPumpCarnot | - | - | Template name (shortened) |
| T_a2_nominal | 313.15 | K | HeatPumpCarnot | Nominal return temperature |
| T_b1_nominal | 343.15 | K | HeatPumpCarnot | Nominal supply temperature |
| Q_flow_input | @input_heat | W | HeatPumpCarnot | Heat demand (CONNECTOR) |

**Template Name Formats:**
- **Short name**: `SourceIdeal` (automatically expands to full path)
- **Full name**: `AixLib_Fluid_DistrictHeatingCooling_Supplies_OpenLoop_SourceIdeal`
- **Custom path**: `/absolute/path/to/custom_template.mako`

---

## Parameter Types and Priorities

### Parameter Categories

Each Modelica template defines three categories of parameters:

```mako
<%def name="get_main_parameters()">
   pReturn TReturn
</%def>

<%def name="get_aux_parameters()">
   allowFlowReversal
</%def>

<%def name="get_connector_names()">
   TIn dpIn
</%def>
```

| Category | Required? | Validation | Default Behavior |
|----------|-----------|------------|------------------|
| **MAIN** | ✅ Yes | ValueError if missing | No defaults |
| **AUX** | ❌ No | UserWarning if missing | Modelica defaults used |
| **CONNECTORS** | ✅ Yes | ValueError if missing | No defaults |

### Parameter Priority (What Overwrites What?)

The pipeline follows this priority order:

```
1. Graph attributes (highest priority)
   ↓ (if not found)
2. Excel values
   ↓ (if not found)
3. Modelica defaults (AUX parameters only)
   ↓ (if not found)
4. ERROR (MAIN and CONNECTORS)
```

**Key Rule**: *"What's already there doesn't get overwritten"*

If a parameter already exists in the graph (e.g., set programmatically), the Excel value is **ignored**.

### Example Priority Resolution

```python
# Scenario: pReturn parameter for supply node

# Priority 1: Check graph
if 'pReturn' in uesgraph.nodes['supply1']:
    value = uesgraph.nodes['supply1']['pReturn']  # ← Use this!
    # Excel value is ignored

# Priority 2: Check Excel
elif 'pReturn' in excel_params:
    value = excel_params['pReturn']  # ← Use this!
    uesgraph.nodes['supply1']['pReturn'] = value

# Priority 3: Error (MAIN parameter)
else:
    raise ValueError("Missing MAIN parameter: pReturn")
```

---

## Type Conversion

The pipeline automatically converts Excel values to appropriate Python types.

### Automatic Conversions

| Excel Value | Python Type | Notes |
|-------------|-------------|-------|
| `123` | `int` | Integer numbers |
| `123.45` | `float` | Decimal numbers |
| `1e5` | `float` | Scientific notation → 100000.0 |
| `1.23e-4` | `float` | Negative exponent → 0.000123 |
| `TRUE` / `FALSE` | `bool` | Case-insensitive |
| `template_name` | `str` | Text values |
| `@diameter` | `str` | References kept as strings |
| `/path/to/file` | `str` | Paths kept as strings |

### Why This Matters

**Problem**: Excel can format cells as "Text", causing numeric values to be read as strings:
```python
pReturn = '1e5'  # ← String, not number!
round(pReturn, 10)  # ← ERROR: str has no __round__ method
```

**Solution**: Automatic conversion in `load_component_parameters()`:
```python
pReturn = '1e5'  # From Excel
→ 100000.0  # After conversion
```

### Edge Cases Handled

✅ Template names with dots: `AixLib.Fluid.DistrictHeating...` → stays string
✅ @references: `@diameter` → stays string
✅ File paths: `/home/user/template.mako` → stays string
✅ Mixed notation: `1.5e3` → 1500.0

---

## Connector Handling

### What Are Connectors?

**Connectors** are time-series inputs to Modelica components. Unlike static parameters (which have a single value), connectors provide dynamic input over time.

**Examples:**
- **TIn**: Supply temperature profile over 1 year
- **dpIn**: Pressure difference profile
- **Q_flow_input**: Heat demand profile

### How Connectors Work

1. **Definition in Template**:
```mako
Modelica.Blocks.Interfaces.RealInput ${str(name + 'TIn')}
```

2. **CSV File Generation**:
The pipeline creates CSV files for each connector:
```
workspace/models/Sim20250106_123456/supply1TIn.csv
```

3. **Modelica Integration**:
```modelica
Modelica.Blocks.Tables.CombiTimeTable supply1TIn(
  tableName="tab1",
  fileName="supply1TIn.csv"
)
```

### Connector Value Types

#### 1. Scalar Values (Most Common)

Excel value is a single number → automatically converted to **constant time-series**:

```python
# Excel: TIn = 353.15

# Pipeline converts to:
TIn = [353.15, 353.15, 353.15, ..., 353.15]  # 8760 values for 1 year
```

**Time array calculation**:
```python
timestep = 900  # 15 minutes
stop_time = 86400  # 1 day
time_array = [0, 900, 1800, ..., 86400]  # 97 timesteps
```

#### 2. @References

Reference existing graph attributes (useful for programmatically set values):

```python
# In code: Set node attribute
uesgraph.nodes['supply1']['design_supply_temp'] = 353.15

# Excel: TIn = @design_supply_temp
# → Resolves to 353.15, then converted to time-series
```

#### 3. Future: CSV File Paths (TODO)

Planned feature for loading custom time-series:

```python
# Excel: TIn = /path/to/temperature_profile.csv
# → Load CSV and use as time-series (not yet implemented)
```

---

### Special Case: Demand Connectors

**Demands follow a special convention** to maintain backward compatibility with the legacy hardcoded system.

#### The Convention

Demand time-series data uses standardized attribute names:
- `input_heat`: Heating demand profile
- `input_dhw`: Domestic hot water demand profile
- `input_cool`: Cooling demand profile

These are set by `assign_demand_data()` when loading CSV files.

#### How It Works

**Step 1**: Load demand data from CSV
```python
assign_demand_data(uesgraph, {
    'heating': 'demands-heat.csv',
    'dhw': 'demands-dhw.csv',
    'cooling': 'demands-cool.csv'
})

# Result: Sets node['input_heat'], node['input_dhw'], node['input_cool']
```

**Step 2**: Excel maps template connectors to conventions
```
Sheet: Demands
Parameter        Value           Description
Q_flow_input     @input_heat     References heating demand data
```

**Step 3**: Legacy system creates hardcoded files
```python
# Files are automatically created:
workspace/models/.../Resources/Inputs/demand_w11_1_heat.txt
workspace/models/.../Resources/Inputs/demand_w11_1_dhw.txt
```

**Step 4**: System-level templates connect everything
```mako
# demand_inputs.mako - creates CombiTimeTable
fileName="modelica://.../ demand_${name_demand}_heat.txt"

# connections_demands.mako - connects to component
connect(networkModel.${name_demand}Q_flow_input, ${name_demand}Table.y[1])
```

#### Why This Convention Exists

The demand system is **hardcoded** for historical reasons:
- ✅ **Backward compatible** with existing workflows
- ✅ **Proven system** used in production
- ✅ **Automatic file generation** without manual specification
- ⚠️ **Less flexible** than supply system (which uses dynamic connector names)

#### Configuration Example

```
Excel: Demands Sheet
Parameter        Value           Unit    Description
Q_flow_input     @input_heat     W       Heat demand connector
```

This tells the pipeline:
1. Template expects a connector called `Q_flow_input`
2. This connector references `input_heat` attribute
3. Validation checks that `input_heat` exists on nodes
4. Legacy system creates files using `input_heat` data
5. System templates connect everything automatically

#### Key Differences from Supply

| Aspect | Supply Connectors | Demand Connectors |
|--------|------------------|-------------------|
| Naming | Dynamic (from template) | Convention (`input_*`) |
| Files | `supply_${name}_${connector}.txt` | `demand_${name}_heat.txt` |
| System | Fully dynamic | Partially hardcoded |
| Mapping | Direct (connector = attribute) | Via @reference |

#### Templates Without Connectors

Some demand templates (e.g., `SimpleSubstationPumpSecondaryHE`) have **no connectors**:

```mako
<%def name="get_connector_names()">
   # Empty - no connectors!
</%def>
```

These templates:
- Reference files **directly** in component parameters: `fileNameHeat = "..."`
- Use `link_demands_to_ressources = TRUE` flag in Excel
- Skip system-level connection templates
- Handle files internally in the component

**Excel Configuration**:
```
Sheet: Demands
Parameter                    Value
template                     SimpleSubstationPumpSecondaryHE
link_demands_to_ressources   TRUE
```

This is the **cleanest approach** for custom templates that manage their own file loading.

---

### Connector Validation

Missing connectors cause **ValueError** with detailed instructions:

```
Validation FAILED: 2 required connector(s) missing for nodes
Missing connectors: TIn, dpIn

Connectors are time-series inputs required by Modelica templates.

HOW TO FIX:
Option 1 - Define in Excel sheet:
  • Open the Excel configuration file
  • Go to the 'Supply' sheet
  • Add rows: Parameter='TIn', Value=<number or @reference>
  • Example: Parameter='TIn', Value=353.15

Option 2 - Define on UESGraph before calling pipeline:
  • For nodes: uesgraph.nodes[component_id]['TIn'] = value
  • Example: uesgraph.nodes['supply1']['TIn'] = 353.15

Note: Scalar values are automatically converted to constant time-series.
```

---

## Using @References

### What Are @References?

@References allow you to **link Excel parameters to existing graph attributes**. This is useful for:

1. Avoiding duplication (attribute already exists in graph)
2. Maintaining consistency (multiple parameters reference same source)
3. Programmatic control (set attributes in code, reference in Excel)

### Syntax

```
@attribute_name
```

The `@` prefix tells the pipeline to look up `attribute_name` in the component's data dictionary.

### Examples

#### Example 1: Pipe Length

```python
# Excel: Pipes sheet
length = @length

# What happens:
edge_data = uesgraph.edges[(node1, node2)]
# edge_data['length'] = 125.5  (from GeoJSON)

# Resolution:
resolved_value = edge_data['length']  # → 125.5
```

#### Example 2: Demand Heat Input

```python
# Excel: Demands sheet
Q_flow_input = @input_heat

# What happens:
node_data = uesgraph.nodes['building1']
# node_data['input_heat'] = [1000, 1050, 980, ...]  (from assign_demand_data)

# Resolution:
resolved_value = node_data['input_heat']  # → [1000, 1050, ...]
# Already a time-series, no conversion needed
```

#### Example 3: Supply Temperature

```python
# In code: Set attribute before pipeline
uesgraph.nodes['supply1']['design_temp'] = 353.15

# Excel: Supply sheet
TIn = @design_temp

# Resolution:
resolved_value = uesgraph.nodes['supply1']['design_temp']  # → 353.15
# Converted to time-series: [353.15, 353.15, ...]
```

### @Reference Rules

✅ **Works for**: Node attributes, edge attributes, programmatically set values
✅ **Works on**: MAIN, AUX, and CONNECTOR parameters
✅ **Type handling**: Resolved value is checked for type (scalar vs list)
❌ **Error if missing**: `ValueError` if referenced attribute doesn't exist

### Error Handling

```python
# Excel: TIn = @missing_attribute

# Error message:
ValueError: Component supply1: Parameter 'TIn' references
non-existent attribute '@missing_attribute'
```

---

## Complete Workflow Example

### Scenario: District Heating Network from GeoJSON

**Goal**: Generate Modelica model from GeoJSON files with custom parameters.

### Step 1: Prepare Input Files

```
data/
├── network.geojson          # Pipe network topology
├── buildings.geojson        # Building locations
├── supply.geojson           # Supply station
├── demands-heat.csv         # Heating demand time-series
├── demands-dhw.csv          # DHW demand time-series
├── demands-cool.csv         # Cooling demand time-series
└── ground_temps.csv         # Ground temperature profiles
```

### Step 2: Configure Excel Template

**File**: `uesgraphs_parameters_template.xlsx`

**Simulation Sheet**:
```
simulation_name    MyDistrict
stop_time          31536000        # 1 year in seconds
timestep           900             # 15 minutes
```

**Pipes Sheet**:
```
template           PlugFlowPipeEmbedded
diameter           0.15
length             @length         # Reference from GeoJSON
lambda_isolation   0.024
```

**Supply Sheet**:
```
template           SourceIdeal
pReturn            100000          # 1 bar
TReturn            313.15          # 40°C
TIn                353.15          # 80°C (constant supply)
dpIn               100000          # 1 bar differential
```

**Demands Sheet**:
```
template           HeatPumpCarnot
T_a2_nominal       313.15
T_b1_nominal       343.15
Q_flow_input       @input_heat     # Reference from CSV
```

### Step 3: Run Pipeline

```python
from uesgraphs import UESGraph
from uesgraphs.systemmodels.model_generation_pipeline import uesgraph_to_modelica

# Import GeoJSON
graph = UESGraph()
graph.from_geojson(
    network_path='data/network.geojson',
    buildings_path='data/buildings.geojson',
    supply_path='data/supply.geojson',
    name='my_district'
)

# Generate Modelica model
uesgraph_to_modelica(
    uesgraph=graph,
    simplification_level=0,
    workspace='output/',
    sim_setup_path='uesgraphs_parameters_template.xlsx',
    input_heating='data/demands-heat.csv',
    input_dhw='data/demands-dhw.csv',
    input_cooling='data/demands-cool.csv',
    ground_temp_path='data/ground_temps.csv'
)
```

### Step 4: Output Structure

```
output/
├── models/
│   └── Sim20250106_123456_MyDistrict/
│       ├── Sim20250106_123456_MyDistrict.mo   # Main model
│       ├── package.mo                          # Package definition
│       ├── supply1TIn.csv                      # Supply temp connector
│       ├── supply1dpIn.csv                     # Supply pressure connector
│       ├── building1Q_flow_input.csv           # Demand connector
│       └── ...                                 # Other component files
└── transurban_seestadt_uesgraphs_with_demand.json
```

### Step 5: Simulate in Dymola

1. Open Dymola/OpenModelica
2. Load AixLib library
3. Open `Sim20250106_123456_MyDistrict.mo`
4. Click "Simulate"

---

## Troubleshooting

### Common Errors and Solutions

#### Error: "Missing required connector(s)"

```
ValueError: Missing 2 required connector(s) for nodes: TIn, dpIn
```

**Cause**: Template requires connectors that aren't defined.

**Solution**:
1. Open Excel config file
2. Go to relevant sheet (Supply, Demands, Pipes)
3. Add missing parameters:
   ```
   TIn     353.15    K
   dpIn    100000    Pa
   ```

---

#### Error: "type str doesn't define __round__ method"

```
TypeError: type str doesn't define __round__ method
```

**Cause**: Excel cell formatted as "Text" instead of number.

**Solution**:
- ✅ **Automatic**: The new pipeline handles this automatically!
- ✅ Scientific notation `1e5` is converted to `100000.0`
- ✅ Booleans `TRUE`/`FALSE` are converted to `True`/`False`

If error persists, check that `load_component_parameters()` is being used (not old loading method).

---

#### Error: "Connectors found but no time_array available"

```
WARNING: Connectors found but no time_array available (stop_time/timestep not set)
```

**Cause**: `stop_time` or `timestep` not set in simulation settings.

**Solution**:
1. Check Excel 'Simulation' sheet
2. Ensure these parameters exist:
   ```
   stop_time    86400    s
   timestep     900      s
   ```

**Note**: The new pipeline automatically writes these to the graph, so this shouldn't happen anymore.

---

#### Error: "Parameter references non-existent attribute"

```
ValueError: Component supply1: Parameter 'TIn' references
non-existent attribute '@supply_temp'
```

**Cause**: @reference points to attribute that doesn't exist.

**Solution**:
1. Check spelling: `@supply_temp` vs `@supplyTemp`
2. Verify attribute exists in graph:
   ```python
   print(uesgraph.nodes['supply1'].keys())
   ```
3. Set attribute before pipeline if needed:
   ```python
   uesgraph.nodes['supply1']['supply_temp'] = 353.15
   ```

---

#### Warning: "X AUX parameters not provided"

```
UserWarning: 34 AUX parameter(s) not provided for edges,
will use Modelica defaults: allowFlowReversal, linearized, ...
```

**Cause**: Optional (AUX) parameters not specified.

**Impact**: ⚠️ **This is OK!** Modelica will use default values.

**If you want to customize**:
1. Add parameters to Excel sheet
2. Or ignore warning if defaults are acceptable

---

### Debugging Tips

#### 1. Check Log Files

```bash
# Location
/tmp/ModelicaCodeGen_YYYYMMDD_HHMMSS.log

# What to look for
grep "ERROR" /tmp/ModelicaCodeGen_*.log
grep "Missing" /tmp/ModelicaCodeGen_*.log
```

#### 2. Inspect UESGraph

```python
# After import, before pipeline
print(f"Nodes: {len(graph.nodelist_building)}")
print(f"Edges: {graph.number_of_edges()}")

# Check supply node attributes
supply_nodes = [n for n in graph.nodelist_building
                if graph.nodes[n].get('is_supply_heating')]
print(f"Supply attributes: {graph.nodes[supply_nodes[0]].keys()}")
```

#### 3. Validate Excel Loading

```python
from uesgraphs.systemmodels.model_generation_pipeline import load_component_parameters

params = load_component_parameters('path/to/excel.xlsx', 'Supply')
print(f"Loaded parameters: {params.keys()}")
print(f"pReturn type: {type(params['pReturn'])}")  # Should be float
```

#### 4. Test Template Parsing

```python
from uesgraphs.systemmodels.model_generation_pipeline import parse_template_parameters

main, aux, connectors = parse_template_parameters('Supply', 'SourceIdeal')
print(f"MAIN: {main}")
print(f"AUX: {aux}")
print(f"CONNECTORS: {connectors}")
```

---

## Migration from Old Pipeline

### Key Differences

| Aspect | Old Pipeline | New Pipeline |
|--------|--------------|--------------|
| Config | Multiple files/code | Single Excel file |
| Connectors | Manual handling | Automatic |
| Type conversion | Manual | Automatic |
| Validation | Partial | Comprehensive |
| Error messages | Generic | Detailed with fixes |
| @References | Not supported | Full support |

### Migration Steps

1. **Create Excel config** from old parameters
2. **Update function call** to `uesgraph_to_modelica()`
3. **Remove manual connector handling** (now automatic)
4. **Test with your data** (use integration test as template)

### Example Migration

**Old code**:
```python
# Old: utilities.prepare_graph()
from uesgraphs.systemmodels import utilities as sysmod_utils
uesgraph = sysmod_utils.prepare_graph(
    uesgraph,
    sim_params,
    input_heating,
    # ... many parameters ...
)
```

**New code**:
```python
# New: uesgraph_to_modelica()
from uesgraphs.systemmodels.model_generation_pipeline import uesgraph_to_modelica
uesgraph_to_modelica(
    uesgraph=uesgraph,
    workspace='output/',
    sim_setup_path='config.xlsx',
    input_heating='demands-heat.csv',
    input_dhw='demands-dhw.csv',
    input_cooling='demands-cool.csv',
    ground_temp_path='ground_temps.csv'
)
```

**Benefits**:
- ✅ 90% less code
- ✅ Centralized configuration
- ✅ Better error handling
- ✅ Automatic connector support

---

## Advanced Topics

### Custom Templates

You can use custom Modelica templates:

```python
# Excel: Supply sheet
template_path    /home/user/custom_supply.mako
```

Requirements:
- Must define `get_main_parameters()`
- Must define `get_aux_parameters()`
- Must define `get_connector_names()`

### Programmatic Parameter Setting

Set parameters in code before pipeline:

```python
# Override Excel values by setting graph attributes
for node in graph.nodelist_building:
    if graph.nodes[node].get('is_supply_heating'):
        graph.nodes[node]['TIn'] = 360.15  # Higher temp
        graph.nodes[node]['pReturn'] = 150000  # Higher pressure

# Excel values will be ignored (priority 1: graph)
```

### Conditional Parameters

Use @references for conditional logic:

```python
# In code: Set different temps for different buildings
for node in graph.nodelist_building:
    if graph.nodes[node].get('building_type') == 'industrial':
        graph.nodes[node]['supply_temp'] = 363.15
    else:
        graph.nodes[node]['supply_temp'] = 353.15

# Excel: Demands sheet
T_b1_nominal = @supply_temp  # Different per building
```

---

## Summary

### Key Takeaways

✅ **Single Excel file** for all configuration
✅ **Automatic connector handling** with scalar→time-series conversion
✅ **Intelligent type conversion** (scientific notation, booleans)
✅ **Clear parameter priorities**: Graph > Excel > Modelica defaults
✅ **@References** for linking parameters to graph attributes
✅ **Comprehensive validation** with helpful error messages
✅ **Seamless GeoJSON workflow** with e16 example

### Next Steps

1. Try the **e16 example** (`examples/e16_complete_geojson_to_modelica.py`)
2. Customize **Excel template** for your scenario
3. Run **tests** to validate your configuration (`pytest tests/test_pipeline.py`)
4. Check **logs** if you encounter issues (`/tmp/ModelicaCodeGen_*.log`)

### Getting Help

- **Examples**: `uesgraphs/examples/e16_*.py`
- **Tests**: `tests/test_pipeline.py`
- **Code**: `uesgraphs/systemmodels/model_generation_pipeline.py`
- **Issues**: https://github.com/RWTH-EBC/uesgraphs/issues

---

*Document version: 1.0 (2025-01-06)*
*Pipeline version: 2.1.1*
