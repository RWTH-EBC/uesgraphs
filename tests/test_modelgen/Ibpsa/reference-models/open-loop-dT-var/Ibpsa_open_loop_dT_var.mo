model Ibpsa_open_loop_dT_var
  "Model automatically generated with uesmodels at 2021-02-15 17:57:52.082261"

  package Medium = AixLib.Media.Specialized.Water.ConstantProperties_pT(
    T_nominal=353.15,
    p_nominal=500000.0,
    T_default=353.15
  );
  AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal supplysupply(
    redeclare package Medium = Medium,
    pReturn = 200000.0,
    TReturn = 323.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={400.0,112.5926})));

  Modelica.Blocks.Interfaces.RealInput supplyTIn
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={425.0,137.5926}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={100,90.0})
      ));

  Modelica.Blocks.Interfaces.RealInput supplydpIn
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={425.0,127.5926}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={100,100.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp demandpoint_2(
    redeclare package Medium = Medium,
    Q_flow_nominal = 22719.1187,
    dTDesign = 30,
    TReturn = 323.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={0.0,337.7778})));

  Modelica.Blocks.Interfaces.RealInput point_2Q_flow_input
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={25.0,362.7778}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={-100,90.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp demandpoint_3(
    redeclare package Medium = Medium,
    Q_flow_nominal = 13932.72,
    dTDesign = 30,
    TReturn = 323.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={0.0,0.0})));

  Modelica.Blocks.Interfaces.RealInput point_3Q_flow_input
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={25.0,25.0}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={-100,0.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp demandpoint_4(
    redeclare package Medium = Medium,
    Q_flow_nominal = 19330.08,
    dTDesign = 30,
    TReturn = 323.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={59.2593,198.5185})));

  Modelica.Blocks.Interfaces.RealInput point_4Q_flow_input
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={84.2593,223.5185}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={-100,-90.0})
      ));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10011005(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 4.7636,
    fac = 1,
    length = 115,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 2
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 180.0,
      origin={229.6296,112.5926})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10011005R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 4.7636,
    fac = 1,
    length = 115,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 2
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 180.0,
      origin={224.6296,107.5926})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10021006(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 5.0699,
    fac = 1,
    length = 76,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 2
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 270.0,
      origin={0.0,225.1852})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10021006R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 5.0699,
    fac = 1,
    length = 76,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 2
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 270.0,
      origin={-5.0,220.1852})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10031006(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 5.0699,
    fac = 1,
    length = 38,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 90.0,
      origin={0.0,56.2963})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10031006R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 5.0699,
    fac = 1,
    length = 38,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 90.0,
      origin={-5.0,51.2963})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10041005(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 5.0699,
    fac = 1,
    length = 29,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 270.0,
      origin={59.2593,155.5556})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10041005R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 5.0699,
    fac = 1,
    length = 29,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 270.0,
      origin={54.2593,150.5556})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10051006(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 4.7636,
    fac = 1,
    length = 20,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 180.0,
      origin={29.6296,112.5926})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe10051006R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    cPip = 500,
    rhoPip = 8000,
    thickness = 0.0032,
    R = 4.7636,
    fac = 1,
    length = 20,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 180.0,
      origin={24.6296,107.5926})));

  Modelica.Thermal.HeatTransfer.Sources.PrescribedTemperature TGround
    "Ground temperature for network"
      annotation(Placement(transformation(
      extent={{-2, -2},{2, 2}},
      origin={5, 5})));

  Modelica.Blocks.Interfaces.RealInput TGroundIn(unit="K")
    "Input of prescribed ground temperature"
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={{0, 0}}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=90,
        origin={0, -100})
      ));



equation
  connect(supplysupply.port_b, pipe10011005.port_a)
    annotation(Line(points={{400.0,112.59259259259258},{224.62962962962962,107.59259259259258}}, color={0,127,255}, thickness=0.5));
  connect(supplysupply.port_a, pipe10011005R.port_a)
    annotation(Line(points={{395.0,107.59259259259258},{219.62962962962962,102.59259259259258}}, color={0,127,255}, thickness=0.5));
  connect(demandpoint_2.port_a, pipe10021006.port_a)
    annotation(Line(points={{0.0,337.77777777777777},{-5.0,220.18518518518513}}, color={0,127,255}, thickness=0.5));
  connect(demandpoint_2.port_b, pipe10021006R.port_a)
    annotation(Line(points={{-5.0,332.77777777777777},{-10.0,215.18518518518513}}, color={0,127,255}, thickness=0.5));
  connect(demandpoint_3.port_a, pipe10031006.port_a)
    annotation(Line(points={{0.0,0.0},{-5.0,51.29629629629629}}, color={0,127,255}, thickness=0.5));
  connect(demandpoint_3.port_b, pipe10031006R.port_a)
    annotation(Line(points={{-5.0,-5.0},{-10.0,46.29629629629629}}, color={0,127,255}, thickness=0.5));
  connect(demandpoint_4.port_a, pipe10041005.port_a)
    annotation(Line(points={{59.25925925925925,198.51851851851853},{54.25925925925925,150.55555555555554}}, color={0,127,255}, thickness=0.5));
  connect(demandpoint_4.port_b, pipe10041005R.port_a)
    annotation(Line(points={{54.25925925925925,193.51851851851853},{49.25925925925925,145.55555555555554}}, color={0,127,255}, thickness=0.5));
  connect(pipe10011005.ports_b[1], pipe10041005.ports_b[1])
    annotation(Line(points={{224.62962962962962,107.59259259259258},{54.25925925925925,150.55555555555554}}, color={0,127,255}, thickness=0.5));
  connect(pipe10011005R.ports_b[1], pipe10041005R.ports_b[1])
    annotation(Line(points={{224.62962962962962,107.59259259259258},{54.25925925925925,150.55555555555554}}, color={0,127,255}, thickness=0.5));
  connect(pipe10011005.ports_b[2], pipe10051006.port_a)
    annotation(Line(points={{224.62962962962962,107.59259259259258},{24.629629629629626,107.59259259259258}}, color={0,127,255}, thickness=0.5));
  connect(pipe10011005R.ports_b[2], pipe10051006R.port_a)
    annotation(Line(points={{224.62962962962962,107.59259259259258},{24.629629629629626,107.59259259259258}}, color={0,127,255}, thickness=0.5));
  connect(pipe10021006.ports_b[1], pipe10031006.ports_b[1])
    annotation(Line(points={{-5.0,220.18518518518513},{-5.0,51.29629629629629}}, color={0,127,255}, thickness=0.5));
  connect(pipe10021006R.ports_b[1], pipe10031006R.ports_b[1])
    annotation(Line(points={{-5.0,220.18518518518513},{-5.0,51.29629629629629}}, color={0,127,255}, thickness=0.5));
  connect(pipe10021006.ports_b[2], pipe10051006.ports_b[1])
    annotation(Line(points={{-5.0,220.18518518518513},{24.629629629629626,107.59259259259258}}, color={0,127,255}, thickness=0.5));
  connect(pipe10021006R.ports_b[2], pipe10051006R.ports_b[1])
    annotation(Line(points={{-5.0,220.18518518518513},{24.629629629629626,107.59259259259258}}, color={0,127,255}, thickness=0.5));

  connect(point_2Q_flow_input, demandpoint_2.Q_flow_input);
  connect(point_3Q_flow_input, demandpoint_3.Q_flow_input);
  connect(point_4Q_flow_input, demandpoint_4.Q_flow_input);

  connect(supplyTIn, supplysupply.TIn);
  connect(supplydpIn, supplysupply.dpIn);

  connect(TGroundIn, TGround.T);

  connect(TGround.port, pipe10011005.heatPort);
  connect(TGround.port, pipe10011005R.heatPort);
  connect(TGround.port, pipe10021006.heatPort);
  connect(TGround.port, pipe10021006R.heatPort);
  connect(TGround.port, pipe10031006.heatPort);
  connect(TGround.port, pipe10031006R.heatPort);
  connect(TGround.port, pipe10041005.heatPort);
  connect(TGround.port, pipe10041005R.heatPort);
  connect(TGround.port, pipe10051006.heatPort);
  connect(TGround.port, pipe10051006R.heatPort);

  annotation (
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{0.0,0.0},{400.0,337.77777777777777}})),
    uses(AixLib),
    Documentation(
      info="<html>
      <p>Network model generated with uesmodels</p>
      </html>", revisions="<html>
      <ul>
        <li><i>February 15, 2021&nbsp;</i> uesmodels v0.8.3:<br/>Auto-generated.</li>
      </ul>
      </html>"
    ),
    experiment(
      Tolerance=1e-05,
      StopTime=603900,
      Interval=900,
      __Dymola_Algorithm="Cvode",
      __Dymola_experimentSetupOutput(events=false)
    )
  );
end Ibpsa_open_loop_dT_var;
