  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDpFixedTempDifferenceBypass demand${str(name)}(
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
    allowFlowReversal = ${str(round(allowFlowReversal, 4))},
    %endif
    Q_flow_nominal = ${str(round(Q_flow_nominal, 4))},
    dTDesign = ${str(round(dTDesign, 4))},
    m_flo_bypass = ${str(round(m_flo_bypass, 4))}
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={${str(round(x, 4))},${str(round(y, 4))}})));

  Modelica.Blocks.Interfaces.RealInput ${str(name + 'Q_flow_input')}
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${str(round(x+25, 4))},${str(round(y+25, 4))}}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${str(-100)},${str(round(90 - i*180/(max(number_of_instances-1.0, 1.0)) + 0, 4))}})
      ));
<%def name="get_main_parameters()">
   Q_flow_nominal dTDesign m_flo_bypass
</%def><%def name="get_aux_parameters()">
   dp_nominal deltaM tau energyDynamics massDynamics sta_default cp_default m_flow_nominal m_flow_small show_T _m_flow_start _dp_start allowFlowReversal
</%def><%def name="get_connector_names()">
   Q_flow_input
</%def>