  AixLib.Fluid.DistrictHeatingCooling.Demands.ClosedLoop.SubstationHeating demand${str(name)}(
    redeclare package Medium = Medium,
    %if cp_default is not None:
    cp_default = ${str(round(cp_default, 4))},
    %endif
    %if m_flow_nominal is not None:
    m_flow_nominal = ${str(round(m_flow_nominal, 4))},
    %endif
    heatDemand_max = ${str(round(heatDemand_max, 4))},
    deltaT_heatingSet = ${str(round(deltaT_heatingSet, 4))},
    deltaT_heatingGridSet = ${str(round(deltaT_heatingGridSet, 4))},
    dp_nominal = ${str(round(dp_nominal, 4))}
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

  Modelica.Blocks.Interfaces.RealInput ${str(name + 'T_supplyHeatingSet')}
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
   heatDemand_max deltaT_heatingSet deltaT_heatingGridSet dp_nominal
</%def><%def name="get_aux_parameters()">
   cp_default m_flow_nominal
</%def><%def name="get_connector_names()">
   heatDemand T_supplyHeatingSet
</%def>