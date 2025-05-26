# Hydraulic Network Sizing in UESGraphs

A physics-based approach for automated mass flow calculation and pipe sizing in district heating networks.

## Quick Start
```python
import uesgraphs.systemmodels.utilities as sysm_ut

# Size your network in one command
sized_graph = sysm_ut.size_hydronic_network(
    graph=your_graph,
    catalog="isoplus",  # Pipe manufacturer catalog
    dT_attribute="dT_Network",  # Temperature difference attribute
    network_type="heating"
)
```

## Prerequisites
Your graph needs these node attributes:
- `input_heat`: Thermal demand [W]
- `dT_Network`: Temperature difference [K] 
- `is_supply_heating`: Boolean flag for supply nodes

## How it Works
1. **Mass Flow Calculation**: Uses `m_flow = Q / (cp * ΔT)`
   - Q: Thermal load [W]
   - cp: Specific heat capacity (4184 J/kg·K for water)  
   - ΔT: Temperature difference [K]

2. **Pipe Selection**: Matches flows to manufacturer catalog
   - Selects next larger pipe if no exact match
   - Adds `DN` and `diameter` attributes to edges

## Available Functions
- `estimate_m_flow_demand_based()` - Mass flow calculation only
- `size_hydronic_network()` - Complete sizing workflow
- `load_pipe_catalog()` - Load manufacturer data

## Examples
See our [comprehensive tutorial notebook](../uesgraphs/examples/e15_hydronic_sizing.ipynb) for detailed examples.
