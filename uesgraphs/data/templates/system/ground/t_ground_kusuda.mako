  AixLib.BoundaryConditions.GroundTemperature.GroundTemperatureKusuda TGroundKusuda(
    t_shift=${t_shift},
    alpha=${alpha},
    D=${D},
    T_mean=${round(T_mean, 2)},
    T_amp=${T_amp}
    ) "Undisturbed ground temperature model"
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=90,
      origin={20, -80}
    )));

  Modelica.Thermal.HeatTransfer.Sensors.TemperatureSensor TGroundIn
    "Ground temperature sensor in system model"
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=90,
      origin={20, -50}
    )));
