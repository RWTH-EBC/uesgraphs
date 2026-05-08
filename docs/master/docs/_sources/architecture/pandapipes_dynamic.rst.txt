Dynamic Simulation with pandapipes
==================================

Architecture Documentation
--------------------------

**Version:** ---  
**Last Updated:** ---

--------------

Table of Contents
-----------------

1. `Overview <#overview>`__
2. `Main Idea <#main-idea>`__
3. `Equations <#equations>`__
4. `Pipe Order Scheme <#pipe-order-scheme>`__
5. `Numerical Solver <#numerical-solver>`__
6. `Transient pandapipes approach <#transient-pandapipes-approach>`__

--------------

Overview
--------

The dynamic simulation extends the static hydraulic pandapipes model
with a dynamic temperature calculation. Hydraulic states are solved
at every timestep using pandapipes, while the thermal behaviour of the
network is calculated separately using a time-dependent pipe model.

The resulting thermo-hydraulic states can be used for further analysis,
visualization, and export to UESGraph.

--------------

Main Idea
---------

The simulation combines steady-state hydraulics with dynamic thermal
calculations.

At each timestep:

1. The hydraulic state is solved using pandapipes.
2. Current mass flows and flow directions are extracted.
3. Pipes are sorted according to the flow direction.
4. Pipe temperatures are updated using an implicit Euler scheme.

The ordering of the pipes is necessary because downstream temperatures
depend on already calculated upstream temperatures.

The same network structure and parameters as in the static simulation
are reused, ensuring consistency and modularity between both approaches.

--------------

Equations
---------

Hydraulic calculations are performed using the pandapipes solver.
The thermal simulation is based on a dynamic one-dimensional heat
transport equation including convective heat transport and thermal
losses to the surrounding ground. This is also the main difference to 
the static pandapipes approach, where the temperature is calculated 
based on a steady-state assumption and all calculations are performed 
within the pandapipes framework.

The governing equation is:

.. math::

   \rho c_p \pi D^2 \Delta x
   \frac{\partial T}{\partial t}
   +
   \dot m(x,t)
   \frac{\partial T}{\partial x}
   =
   \alpha \pi D \Delta x
   (T - T_{amb})

where:

* :math:`T` is the fluid temperature,
* :math:`\dot m` is the mass flow,
* :math:`\rho` is the fluid density,
* :math:`c_p` is the specific heat capacity,
* :math:`D` is the inner pipe diameter,
* :math:`\alpha` is the heat transfer coefficient,
* :math:`T_{amb}` is the ambient ground temperature.

For the dynamic-thermal simulation, the equation is discretized in space and
solved using an implicit Euler scheme in time direction.

This results in the following linear equation system:

.. math::

   -\Delta t F_{conv} T_{i-1}^{n+1}
   +
   \left(
   1 + \Delta t (F_{conv} + F_{loss})
   \right)
   T_i^{n+1}
   =
   T_i^n + \Delta t F_{loss} T_{amb}

with:

.. math::

   F_{conv} =
   \frac{4 \dot m}
   {\rho \pi D^2 \Delta x}

.. math::

   F_{loss} =
   \frac{4 \alpha}
   {\rho D c_p}

The resulting system is solved for every pipe and timestep to obtain
the updated temperature distribution.

--------------

Pipe Order Scheme
-----------------

The temperature calculation requires a physically consistent processing
order because each pipe depends on upstream temperatures.

Before the thermal calculation starts, the current mass flow directions
from the hydraulic solution are evaluated. Pipe directions are updated
automatically if flow reversals occur.

A layer-based graph traversal algorithm is then used to sort the pipes
starting from the heat source and following the mass flow direction.

The supply and return networks are processed separately:

* Supply pipes are ordered from the source to the consumers.
* Return pipes are ordered from the consumers back to the source.

This ordering guarantees that all required upstream temperatures are
already available during the calculation.

The approach is based on the Layer-idea in Qin et al. (2019).

--------------

Numerical Solver
----------------

The dynamic thermal calculation uses an implicit Euler method.

Compared to explicit schemes, the implicit formulation provides improved
numerical stability and allows larger timestep sizes.

For every timestep:

1. Hydraulic states are recalculated.
2. Pipe ordering is updated.
3. Pipe temperatures are solved sequentially.
4. Results are stored in the standard pandapipes result structure.

The calculated results care exported as CSV files and integrated into
UESGraph files for supply and return side.

---

Transient pandapipes approach
-----------------------------

This approach is activated if in the Excel sheet mode is set to "transient" 
and allows transient simulation from pandapipes.
See in pandapipes documentation for more details: https://pandapipes.readthedocs.io/en/latest/

*This document describes the dynamic simulation approach using pandapipes.*
