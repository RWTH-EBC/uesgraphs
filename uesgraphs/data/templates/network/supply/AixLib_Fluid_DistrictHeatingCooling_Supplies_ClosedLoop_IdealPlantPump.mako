  AixLib.Fluid.DistrictHeatingCooling.Supplies.ClosedLoop.IdealPlantPump supply${str(name)}(
    redeclare package Medium = Medium,
    %if dp_nominal is not None:
    dp_nominal = ${str(round(dp_nominal, 4))},
    %endif
    %if m_flow_nominal is not None:
    m_flow_nominal = ${str(round(m_flow_nominal, 4))},
    %endif
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={${str(round(x, 4))},${str(round(y, 4))}})));

  Modelica.Blocks.Interfaces.RealInput ${str(name + 'TIn')}
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${str(round(x+25, 4))},${str(round(y+25, 4))}}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${str(100)},${str(round(90 - i*180/(max(number_of_instances-1.0, 1.0)) + 0, 4))}})
      ));

  Modelica.Blocks.Interfaces.RealInput ${str(name + 'dpIn')}
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${str(round(x+25, 4))},${str(round(y+15, 4))}}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={${str(100)},${str(round(90 - i*180/(max(number_of_instances-1.0, 1.0)) + 10, 4))}})
      ));
<%def name="get_main_parameters()">
   
</%def><%def name="get_aux_parameters()">
   dp_nominal m_flow_nominal
</%def><%def name="get_connector_names()">
   TIn dpIn
</%def>