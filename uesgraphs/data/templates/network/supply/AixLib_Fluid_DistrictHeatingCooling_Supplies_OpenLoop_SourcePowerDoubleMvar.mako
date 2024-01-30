  AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourcePowerDoubleMvar supply${str(name)}(
    redeclare package Medium = Medium,
    %if sta_default is not None:
    sta_default = ${str(round(sta_default, 4))},
    %endif
    %if cp_default is not None:
    cp_default = ${str(round(cp_default, 4))},
    %endif
    %if allowFlowReversal is not None:
    allowFlowReversal = ${str(round(allowFlowReversal, 4))},
    %endif
    pReturn = ${str(round(pReturn, 4))}
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
        origin={${str(100)},${str(round(90 - i*180/(max(number_of_instances-1.0, 1.0)) + 0, 4))}})
      ));
<%def name="get_main_parameters()">
   pReturn
</%def><%def name="get_aux_parameters()">
   sta_default cp_default allowFlowReversal
</%def><%def name="get_connector_names()">
   Q_flow_input
</%def>