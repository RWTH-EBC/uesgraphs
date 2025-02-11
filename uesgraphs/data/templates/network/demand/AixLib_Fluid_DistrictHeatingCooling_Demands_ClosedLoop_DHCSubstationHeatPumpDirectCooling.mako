  AixLib.Fluid.DistrictHeatingCooling.Demands.ClosedLoop.DHCSubstationHeatPumpDirectCooling demand${str(name)}(
    redeclare package Medium = Medium,
    %if sta_default is not None:
    sta_default = ${str(round(sta_default, 4))},
    %endif
    %if cp_default is not None:
    cp_default = ${str(round(cp_default, 4))},
    %endif
    %if dp_nominal is not None:
    dp_nominal = ${str(round(dp_nominal, 4))},
    %endif
    %if m_flow_nominal is not None:
    m_flow_nominal = ${str(round(m_flow_nominal, 4))},
    %endif
    %if deltaT_heaSecSet is not None:
    deltaT_heaSecSet = ${str(round(deltaT_heaSecSet, 4))},
    %endif
    %if T_heaSecSet is not None:
    T_heaSecSet = ${str(round(T_heaSecSet, 4))},
    %endif
    %if T_heaPriSet is not None:
    T_heaPriSet = ${str(round(T_heaPriSet, 4))},
    %endif
    %if T_cooPriSet is not None:
    T_cooPriSet = ${str(round(T_cooPriSet, 4))},
    %endif
    heaDem_max = ${str(round(heaDem_max, 4))}
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={${str(round(x, 4))},${str(round(y, 4))}})));

  Modelica.Blocks.Interfaces.RealInput ${str(name + 'heaDem')}
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

  Modelica.Blocks.Interfaces.RealInput ${str(name + 'cooDem')}
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
   heaDem_max
</%def><%def name="get_aux_parameters()">
   sta_default cp_default dp_nominal m_flow_nominal deltaT_heaSecSet T_heaSecSet T_heaPriSet T_cooPriSet
</%def><%def name="get_connector_names()">
   heaDem cooDem
</%def>