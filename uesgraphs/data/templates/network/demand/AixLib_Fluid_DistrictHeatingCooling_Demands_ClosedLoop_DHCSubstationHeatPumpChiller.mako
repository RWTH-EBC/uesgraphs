  AixLib.Fluid.DistrictHeatingCooling.Demands.ClosedLoop.DHCSubstationHeatPumpChiller demand${str(name)}(
    redeclare package Medium = Medium,
    %if sta_default is not None:
    sta_default = ${str(round(sta_default, 4))},
    %endif
    %if cp_default is not None:
    cp_default = ${str(round(cp_default, 4))},
    %endif
    %if m_flow_nominal is not None:
    m_flow_nominal = ${str(round(m_flow_nominal, 4))},
    %endif
    %if T_heatSecSet is not None:
    T_heatSecSet = ${str(round(T_heatSecSet, 4))},
    %endif
    %if T_coolingSecSet is not None:
    T_coolingSecSet = ${str(round(T_coolingSecSet, 4))},
    %endif
    dp_nominal = ${str(round(dp_nominal, 4))},
    heatDemand_max = ${str(round(heatDemand_max, 4))},
    coolingDemand_max = ${str(round(coolingDemand_max, 4))},
    deltaT_heatSecSet = ${str(round(deltaT_heatSecSet, 4))},
    deltaT_coolingSecSet = ${str(round(deltaT_coolingSecSet, 4))},
    deltaT_heatPriSet = ${str(round(deltaT_heatPriSet, 4))},
    deltaT_coolingPriSet = ${str(round(deltaT_coolingPriSet, 4))}
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={${str(round(x, 4))},${str(round(y, 4))}})));

  Modelica.Blocks.Interfaces.RealInput ${str(name + 'heatDemand')}
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${str(round(x+25, 4))},${str(round(y+25, 4))}}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${-100},${str(round(90 - i*180/(max(number_of_instances-1.0, 1.0)) + 0, 4))}})
      ));

  Modelica.Blocks.Interfaces.RealInput ${str(name + 'coolingDemand')}
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${str(round(x+25, 4))},${str(round(y+15, 4))}}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${-100},${str(round(90 - i*180/(max(number_of_instances-1.0, 1.0)) + 10, 4))}})
      ));
<%def name="get_main_parameters()">
   dp_nominal heatDemand_max coolingDemand_max deltaT_heatSecSet deltaT_coolingSecSet deltaT_heatPriSet deltaT_coolingPriSet
</%def><%def name="get_aux_parameters()">
   sta_default cp_default m_flow_nominal T_heatSecSet T_coolingSecSet
</%def><%def name="get_connector_names()">
   heatDemand coolingDemand
</%def>