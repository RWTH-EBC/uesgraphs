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

