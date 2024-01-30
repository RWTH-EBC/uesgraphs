  AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal supply${str(name)}(
    redeclare package Medium = Medium,
    %if allowFlowReversal is not None:
    allowFlowReversal = ${str(round(allowFlowReversal, 4))},
    %endif
    pReturn = ${str(round(pReturn, 4))},
    TReturn = ${str(round(TReturn, 4))}
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
   pReturn TReturn
</%def><%def name="get_aux_parameters()">
   allowFlowReversal
</%def><%def name="get_connector_names()">
   TIn dpIn
</%def>