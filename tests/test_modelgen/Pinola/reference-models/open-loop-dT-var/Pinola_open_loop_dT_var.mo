model Pinola_open_loop_dT_var
  "Model automatically generated with uesgraphs version 2.1.1 at 2025-11-13 13:09:42.111265"

  package Medium = AixLib.Media.Specialized.Water.ConstantProperties_pT(
    T_nominal=353.15,
    p_nominal=500000.0,
    T_default=353.15
  );
  AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal supplyS1(
    redeclare package Medium = Medium,
    pReturn = 200000.0,
    TReturn = 323.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={0.0,114.2857142857})));

  Modelica.Blocks.Interfaces.RealInput S1TIn
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={25.0,139.2857142857}),
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
        origin={25.0,129.2857142857}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={100,100.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal supplyS2(
    redeclare package Medium = Medium,
    pReturn = 200000.0,
    TReturn = 323.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={380.9523809524,0.0})));

  Modelica.Blocks.Interfaces.RealInput S2TIn
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={405.9523809524,25.0}),
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
        origin={405.9523809524,15.0}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={100,-80.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp demandB1(
    redeclare package Medium = Medium,
    Q_flow_nominal = 22719.1187448,
    dTDesign = 30,
    TReturn = 323.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={64.7619047619,217.1428571429})));

  Modelica.Blocks.Interfaces.RealInput B1Q_flow_input
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={89.7619047619,242.1428571429}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={-100,90.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp demandB2(
    redeclare package Medium = Medium,
    Q_flow_nominal = 13932.72,
    dTDesign = 30,
    TReturn = 323.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={285.7142857143,285.7142857143})));

  Modelica.Blocks.Interfaces.RealInput B2Q_flow_input
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={310.7142857143,310.7142857143}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={-100,0.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp demandB3(
    redeclare package Medium = Medium,
    Q_flow_nominal = 19330.08,
    dTDesign = 30,
    TReturn = 323.15
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={400.0,95.2380952381})));

  Modelica.Blocks.Interfaces.RealInput B3Q_flow_input
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={425.0,120.2380952381}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={-100,-90.0})
      ));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe1(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 155,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={47.619047619,152.380952381})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe1R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 155,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={42.619047619,147.380952381})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe5(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 175,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={371.4285714286,38.0952380952})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe5R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 175,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={366.4285714286,33.0952380952})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe6(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={80.0,203.8095238095})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe6R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={75.0,198.8095238095})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe7(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={285.7142857143,266.6666666667})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe7R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={280.7142857143,261.6666666667})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe8(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={380.9523809524,85.7142857143})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe8R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 15,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={375.9523809524,80.7142857143})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe2(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 100,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={190.4761904762,219.0476190476})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe2R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 100,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={185.4761904762,214.0476190476})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe4(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 45,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={228.5714285714,133.3333333333})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe4R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 45,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={223.5714285714,128.3333333333})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe3(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 70,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={323.8095238095,161.9047619048})));

  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe3R(
    redeclare package Medium = Medium,
    m_flow_nominal = 1,
    fac = 1,
    length = 70,
    dIns = 0.045,
    kIns = 0.024
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={318.8095238095,156.9047619048})));

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
  connect(pipe1.port_b, pipe6.port_b)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{75.0,198.8095238095238}}, color={0,127,255}, thickness=0.5));
  connect(pipe1R.port_b, pipe6R.port_b)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{75.0,198.8095238095238}}, color={0,127,255}, thickness=0.5));
  connect(pipe1.port_b, pipe2.port_a)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{185.47619047619048,214.04761904761907}}, color={0,127,255}, thickness=0.5));
  connect(pipe1R.port_b, pipe2R.port_a)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{185.47619047619048,214.04761904761907}}, color={0,127,255}, thickness=0.5));
  connect(pipe1.port_b, pipe4.port_a)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{223.5714285714286,128.33333333333334}}, color={0,127,255}, thickness=0.5));
  connect(pipe1R.port_b, pipe4R.port_a)
    annotation(Line(points={{42.61904761904761,147.38095238095238},{223.5714285714286,128.33333333333334}}, color={0,127,255}, thickness=0.5));
  connect(pipe5.port_b, pipe8.port_b)
    annotation(Line(points={{366.42857142857144,33.095238095238095},{375.95238095238096,80.71428571428572}}, color={0,127,255}, thickness=0.5));
  connect(pipe5R.port_b, pipe8R.port_b)
    annotation(Line(points={{366.42857142857144,33.095238095238095},{375.95238095238096,80.71428571428572}}, color={0,127,255}, thickness=0.5));
  connect(pipe5.port_b, pipe4.port_b)
    annotation(Line(points={{366.42857142857144,33.095238095238095},{223.5714285714286,128.33333333333334}}, color={0,127,255}, thickness=0.5));
  connect(pipe5R.port_b, pipe4R.port_b)
    annotation(Line(points={{366.42857142857144,33.095238095238095},{223.5714285714286,128.33333333333334}}, color={0,127,255}, thickness=0.5));
  connect(pipe5.port_b, pipe3.port_b)
    annotation(Line(points={{366.42857142857144,33.095238095238095},{318.80952380952385,156.9047619047619}}, color={0,127,255}, thickness=0.5));
  connect(pipe5R.port_b, pipe3R.port_b)
    annotation(Line(points={{366.42857142857144,33.095238095238095},{318.80952380952385,156.9047619047619}}, color={0,127,255}, thickness=0.5));
  connect(pipe7.port_b, pipe2.port_b)
    annotation(Line(points={{280.7142857142857,261.6666666666667},{185.47619047619048,214.04761904761907}}, color={0,127,255}, thickness=0.5));
  connect(pipe7R.port_b, pipe2R.port_b)
    annotation(Line(points={{280.7142857142857,261.6666666666667},{185.47619047619048,214.04761904761907}}, color={0,127,255}, thickness=0.5));
  connect(pipe7.port_b, pipe3.port_a)
    annotation(Line(points={{280.7142857142857,261.6666666666667},{318.80952380952385,156.9047619047619}}, color={0,127,255}, thickness=0.5));
  connect(pipe7R.port_b, pipe3R.port_a)
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
      <p>Network model generated with uesgraphs</p>
      </html>", revisions="<html>
      <ul>
        <li><i>November 13, 2025&nbsp;</i> uesgraphs v2.1.1:<br/>Auto-generated.</li>
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
end Pinola_open_loop_dT_var;
