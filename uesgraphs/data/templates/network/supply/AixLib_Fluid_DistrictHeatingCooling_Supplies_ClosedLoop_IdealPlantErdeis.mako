  AixLib.Fluid.DistrictHeatingCooling.Supplies.ClosedLoop.IdealPlantErdeis supply${str(name)}(
    %if dp_nominal is None and m_flow_nominal is None:
    redeclare package Medium = Medium
    %else:
    redeclare package Medium = Medium,
    %endif
    %if dp_nominal is not None:
    dp_nominal = ${str(round(dp_nominal, 4))},
    %endif
    %if dp_heater is not None:
    dp_heater = ${str(round(dp_heater, 4))},
    %endif
    %if m_flow_nominal is not None:
    m_flow_nominal = ${str(round(m_flow_nominal, 4))},
    %endif
    %if allowFlowReversal is not None:
    allowFlowReversal = ${str(allowFlowReversal).replace("T","t").replace("F","f")},
    %endif
    %if dpRes_nominal is not None:
    dpRes_nominal = ${str(round(dpRes_nominal, 4))},
    %endif
    dh = ${str(round(dh, 4))},
    length = ${str(round(length, 4))}
    )
    annotation(Placement(transformation(
      extent={{-4,-4},{4,4}},
      rotation=0,
      origin={${str(round(x, 4))},${str(round(y, 4))}})));

  Modelica.Blocks.Interfaces.RealInput ${str(name + 'TIn')}
    annotation(Placement(
      transformation(
        extent={{-4,-4},{4,4}},
        rotation=0,
        origin={${str(round(x+25, 4))},${str(round(y+25, 4))}}),
      iconTransformation(
        extent={{-4,-4},{4,4}},
        rotation=0,
        origin={${str(100)},${str(round(90 - i*180/(max(number_of_instances-1.0, 1.0)) + 0, 4))}})
      ));
<%def name="get_main_parameters()">
   dh length
</%def><%def name="get_aux_parameters()">
   dp_nominal dp_heater m_flow_nominal dpRes_nominal allowFlowReversal
</%def><%def name="get_connector_names()">
   TIn
</%def>