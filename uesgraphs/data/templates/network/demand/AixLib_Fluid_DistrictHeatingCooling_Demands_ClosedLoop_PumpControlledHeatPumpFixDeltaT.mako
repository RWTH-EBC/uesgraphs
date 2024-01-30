  AixLib.Fluid.DistrictHeatingCooling.Demands.ClosedLoop.PumpControlledHeatPumpFixDeltaT demand${str(name)}(
    redeclare package MediumBuilding = MediumBuilding,
    redeclare package Medium = Medium,
    %if dp_nominal is not None:
    dp_nominal = ${str(round(dp_nominal, 4))},
    %endif
    %if deltaM is not None:
    deltaM = ${str(round(deltaM, 4))},
    %endif
    %if tau is not None:
    tau = ${str(round(tau, 4))},
    %endif
    %if energyDynamics is not None:
    energyDynamics = ${str(round(energyDynamics, 4))},
    %endif
    %if massDynamics is not None:
    massDynamics = ${str(round(massDynamics, 4))},
    %endif
    %if sta_default is not None:
    sta_default = ${str(round(sta_default, 4))},
    %endif
    %if cp_default is not None:
    cp_default = ${str(round(cp_default, 4))},
    %endif
    %if cp_default_building is not None:
    cp_default_building = ${str(round(cp_default_building, 4))},
    %endif
    %if dTEva_nominal is not None:
    dTEva_nominal = ${str(round(dTEva_nominal, 4))},
    %endif
    %if dTCon_nominal is not None:
    dTCon_nominal = ${str(round(dTCon_nominal, 4))},
    %endif
    %if m_flow_nominal is not None:
    m_flow_nominal = ${str(round(m_flow_nominal, 4))},
    %endif
    %if m_flow_small is not None:
    m_flow_small = ${str(round(m_flow_small, 4))},
    %endif
    %if show_T is not None:
    show_T = ${str(round(show_T, 4))},
    %endif
    %if _m_flow_start is not None:
    _m_flow_start = ${str(round(_m_flow_start, 4))},
    %endif
    %if _dp_start is not None:
    _dp_start = ${str(round(_dp_start, 4))},
    %endif
    %if allowFlowReversal is not None:
    allowFlowReversal = ${str(allowFlowReversal).replace("T","t").replace("F","f")},
    %endif
    %if k is not None:
    k = ${str(round(k, 4))},
    %endif
    %if Ti is not None:
    Ti = ${str(round(Ti, 4))},
    %endif
    %if yMax is not None and isinstance(yMax, str):
    yMax = ${str(yMax)},
    %elif yMax is not None:
    yMax = ${str(round(yMax, 4))},
    %endif
    %if yMin is not None:
    yMin = ${str(round(yMin, 4))},
    %endif
    %if y_start is not None:
    y_start = ${str(round(y_start, 4))},
    %endif
    Q_flow_nominal = ${str(round(Q_flow_nominal, 4))},
    dTBuilding = ${str(round(dTBuilding, 4))},
    TSupplyBuilding = ${str(round(TSupplyBuilding, 4))},
    TReturn = ${str(round(TReturn, 4))},
    dTDesign = ${str(round(dTDesign, 4))}
    )
    annotation(Placement(transformation(
      extent={{-4,-4},{4,4}},
      rotation=0,
      origin={${str(round(x, 4))},${str(round(y, 4))}})));
  Modelica.Blocks.Interfaces.RealInput ${str(name + 'Q_flow_input')}
    annotation(Placement(
      transformation(
        extent={{-4,-4},{4,4}},
        rotation=0,
        origin={${str(round(x+25, 4))},${str(round(y+25, 4))}}),
      iconTransformation(
        extent={{-4,-4},{4,4}},
        rotation=0,
        origin={${str(-100)},${str(round(90 - i*180/(max(number_of_instances-1.0, 1.0)) + 0, 4))}})
      ));
<%def name="get_main_parameters()">
   Q_flow_nominal dTBuilding TSupplyBuilding TReturn dTDesign
</%def><%def name="get_aux_parameters()">
   dp_nominal deltaM tau energyDynamics massDynamics sta_default cp_default cp_default_building dTEva_nominal dTCon_nominal m_flow_nominal m_flow_small show_T _m_flow_start _dp_start allowFlowReversal k Ti yMax yMin y_start
</%def><%def name="get_connector_names()">
   Q_flow_input
</%def>