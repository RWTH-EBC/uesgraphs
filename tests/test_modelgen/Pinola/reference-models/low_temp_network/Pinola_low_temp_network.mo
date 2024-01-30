model Pinola_low_temp_network
  "Model automatically generated with uesmodels at 2021-02-15 17:57:51.395072"

  package Medium = AixLib.Media.Specialized.Water.ConstantProperties_pT(
    T_nominal=288.15,
    p_nominal=500000.0,
    T_default=288.15
  );
  package MediumBuilding = AixLib.Media.Specialized.Water.ConstantProperties_pT(
    T_nominal=303.15,
    p_nominal=300000.0,
    T_default=303.15
  );
  AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal supplyS1(
    redeclare package Medium = Medium,
    pReturn = 200000.0,
    TReturn = 283.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={0.0,114.2857})));

  Modelica.Blocks.Interfaces.RealInput S1TIn
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={25.0,139.2857}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={100,90.0})
      ));

  Modelica.Blocks.Interfaces.RealInput S1dpIn
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={25.0,129.2857}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={100,100.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal supplyS2(
    redeclare package Medium = Medium,
    pReturn = 200000.0,
    TReturn = 283.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={380.9524,0.0})));

  Modelica.Blocks.Interfaces.RealInput S2TIn
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={405.9524,25.0}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={100,-90.0})
      ));

  Modelica.Blocks.Interfaces.RealInput S2dpIn
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={405.9524,15.0}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={100,-80.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot demandB1(
    redeclare package Medium = Medium,
    redeclare package MediumBuilding = MediumBuilding,
    dp_nominal = 50000,
    Q_flow_nominal = 22719.1187,
    dTDesign = 10,
    TReturn = 283.15,
    dTBuilding = 10,
    TSupplyBuilding = 313.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={64.7619,217.1429})));

  Modelica.Blocks.Interfaces.RealInput B1Q_flow_input
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={89.7619,242.1429}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={-100,90.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot demandB2(
    redeclare package Medium = Medium,
    redeclare package MediumBuilding = MediumBuilding,
    dp_nominal = 50000,
    Q_flow_nominal = 13932.72,
    dTDesign = 10,
    TReturn = 283.15,
    dTBuilding = 10,
    TSupplyBuilding = 313.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={285.7143,285.7143})));

  Modelica.Blocks.Interfaces.RealInput B2Q_flow_input
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={310.7143,310.7143}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={-100,0.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot demandB3(
    redeclare package Medium = Medium,
    redeclare package MediumBuilding = MediumBuilding,
    dp_nominal = 50000,
    Q_flow_nominal = 19330.08,
    dTDesign = 10,
    TReturn = 283.15,
    dTBuilding = 10,
    TSupplyBuilding = 313.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={400.0,95.2381})));

  Modelica.Blocks.Interfaces.RealInput B3Q_flow_input
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={425.0,120.2381}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={-100,-90.0})
      ));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe1(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 155,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 3
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 38.6598,
      origin={47.619,152.381})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe1R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 155,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 3
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 38.6598,
      origin={42.619,147.381})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe5(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 175,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 3
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 104.0362,
      origin={371.4286,38.0952})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe5R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 175,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 3
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 104.0362,
      origin={366.4286,33.0952})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe6(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 318.8141,
      origin={80.0,203.8095})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe6R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 318.8141,
      origin={75.0,198.8095})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe7(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 2
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 270.0,
      origin={285.7143,266.6667})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe7R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 2
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 270.0,
      origin={280.7143,261.6667})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe8(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 206.5651,
      origin={380.9524,85.7143})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe8R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 206.5651,
      origin={375.9524,80.7143})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe2(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 100,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 16.6992,
      origin={190.4762,219.0476})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe2R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 100,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 16.6992,
      origin={185.4762,214.0476})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe4(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 45,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 336.8014,
      origin={228.5714,133.3333})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe4R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 45,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 336.8014,
      origin={223.5714,128.3333})));

  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe3(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 70,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 293.9625,
      origin={323.8095,161.9048})));
  AixLib.Fluid.FixedResistances.PlugFlowPipe pipe3R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 70,
    dIns = 0.045,
    kIns = 0.024,
    nPorts = 1
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
        rotation = 293.9625,
      origin={318.8095,156.9048})));

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
  connect(supplyS1.port_b, pipe1.port_a)
    annotation(Line(points={{0.0,114.28571428571429},{42.61904761904761,147.38095238095238}}, color={0,127,255}, thickness=0.5));
  connect(supplyS1.port_a, pipe1R.port_a)
    annotation(Line(points={{-5.0,109.28571428571429},{37.61904761904761,142.38095238095238}}, color={0,127,255}, thickness=0.5));
  connect(supplyS2.port_b, pipe5.port_a)
    annotation(Line(points={{380.9523809523809,0.0},{366.42857142857144,33.095238095238095}}, color={0,127,255}, thickness=0.5));
  connect(supplyS2.port_a, pipe5R.port_a)
    annotation(Line(points={{375.9523809523809,-5.0},{361.42857142857144,28.095238095238095}}, color={0,127,255}, thickness=0.5));
  connect(demandB1.port_a, pipe6.port_a)
    annotation(Line(points={{64.76190476190476,217.14285714285714},{75.0,198.8095238095238}}, color={0,127,255}, thickness=0.5));
  connect(demandB1.port_b, pipe6R.port_a)
    annotation(Line(points={{59.76190476190476,212.14285714285714},{70.0,193.8095238095238}}, color={0,127,255}, thickness=0.5));
  connect(demandB2.port_a, pipe7.port_a)
    annotation(Line(points={{285.7142857142857,285.7142857142857},{280.7142857142857,261.6666666666667}}, color={0,127,255}, thickness=0.5));
  connect(demandB2.port_b, pipe7R.port_a)
    annotation(Line(points={{280.7142857142857,280.7142857142857},{275.7142857142857,256.6666666666667}}, color={0,127,255}, thickness=0.5));
  connect(demandB3.port_a, pipe8.port_a)
    annotation(Line(points={{400.0,95.23809523809524},{375.95238095238096,80.71428571428572}}, color={0,127,255}, thickness=0.5));
  connect(demandB3.port_b, pipe8R.port_a)
    annotation(Line(points={{395.0,90.23809523809524},{370.95238095238096,75.71428571428572}}, color={0,127,255}, thickness=0.5));
  connect(pipe1.ports_b[1], pipe6.ports_b[1])
    annotation(Line(points={{42.61904761904761,147.38095238095238},{75.0,198.8095238095238}}, color={0,127,255}, thickness=0.5));
  connect(pipe1R.ports_b[1], pipe6R.ports_b[1])
    annotation(Line(points={{42.61904761904761,147.38095238095238},{75.0,198.8095238095238}}, color={0,127,255}, thickness=0.5));
  connect(pipe1.ports_b[2], pipe2.port_a)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{185.47619047619048,214.04761904761907}}, color={0,127,255}, thickness=0.5));
  connect(pipe1R.ports_b[2], pipe2R.port_a)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{185.47619047619048,214.04761904761907}}, color={0,127,255}, thickness=0.5));
  connect(pipe1.ports_b[3], pipe4.port_a)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{223.5714285714286,128.33333333333334}}, color={0,127,255}, thickness=0.5));
  connect(pipe1R.ports_b[3], pipe4R.port_a)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{223.5714285714286,128.33333333333334}}, color={0,127,255}, thickness=0.5));
  connect(pipe5.ports_b[1], pipe8.ports_b[1])
    annotation(Line(points={{366.42857142857144,33.095238095238095},{375.95238095238096,80.71428571428572}}, color={0,127,255}, thickness=0.5));
  connect(pipe5R.ports_b[1], pipe8R.ports_b[1])
    annotation(Line(points={{366.42857142857144,33.095238095238095},{375.95238095238096,80.71428571428572}}, color={0,127,255}, thickness=0.5));
  connect(pipe5.ports_b[2], pipe4.ports_b[1])
    annotation(Line(points={{366.42857142857144,33.095238095238095},{223.5714285714286,128.33333333333334}}, color={0,127,255}, thickness=0.5));
  connect(pipe5R.ports_b[2], pipe4R.ports_b[1])
    annotation(Line(points={{366.42857142857144,33.095238095238095},{223.5714285714286,128.33333333333334}}, color={0,127,255}, thickness=0.5));
  connect(pipe5.ports_b[3], pipe3.ports_b[1])
    annotation(Line(points={{366.42857142857144,33.095238095238095},{318.80952380952385,156.9047619047619}}, color={0,127,255}, thickness=0.5));
  connect(pipe5R.ports_b[3], pipe3R.ports_b[1])
    annotation(Line(points={{366.42857142857144,33.095238095238095},{318.80952380952385,156.9047619047619}}, color={0,127,255}, thickness=0.5));
  connect(pipe7.ports_b[1], pipe2.ports_b[1])
    annotation(Line(points={{280.7142857142857,261.6666666666667},{185.47619047619048,214.04761904761907}}, color={0,127,255}, thickness=0.5));
  connect(pipe7R.ports_b[1], pipe2R.ports_b[1])
    annotation(Line(points={{280.7142857142857,261.6666666666667},{185.47619047619048,214.04761904761907}}, color={0,127,255}, thickness=0.5));
  connect(pipe7.ports_b[2], pipe3.port_a)
    annotation(Line(points={{280.7142857142857,261.6666666666667},{318.80952380952385,156.9047619047619}}, color={0,127,255}, thickness=0.5));
  connect(pipe7R.ports_b[2], pipe3R.port_a)
    annotation(Line(points={{280.7142857142857,261.6666666666667},{318.80952380952385,156.9047619047619}}, color={0,127,255}, thickness=0.5));

  connect(B1Q_flow_input, demandB1.Q_flow_input);
  connect(B2Q_flow_input, demandB2.Q_flow_input);
  connect(B3Q_flow_input, demandB3.Q_flow_input);

  connect(S1TIn, supplyS1.TIn);
  connect(S1dpIn, supplyS1.dpIn);
  connect(S2TIn, supplyS2.TIn);
  connect(S2dpIn, supplyS2.dpIn);

  connect(TGroundIn, TGround.T);

  connect(TGround.port, pipe1.heatPort);
  connect(TGround.port, pipe1R.heatPort);
  connect(TGround.port, pipe5.heatPort);
  connect(TGround.port, pipe5R.heatPort);
  connect(TGround.port, pipe6.heatPort);
  connect(TGround.port, pipe6R.heatPort);
  connect(TGround.port, pipe7.heatPort);
  connect(TGround.port, pipe7R.heatPort);
  connect(TGround.port, pipe8.heatPort);
  connect(TGround.port, pipe8R.heatPort);
  connect(TGround.port, pipe2.heatPort);
  connect(TGround.port, pipe2R.heatPort);
  connect(TGround.port, pipe4.heatPort);
  connect(TGround.port, pipe4R.heatPort);
  connect(TGround.port, pipe3.heatPort);
  connect(TGround.port, pipe3R.heatPort);

  annotation (
    Diagram(coordinateSystem(preserveAspectRatio=false, extent={{0.0,0.0},{400.0,285.7142857142857}})),
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
end Pinola_low_temp_network;
