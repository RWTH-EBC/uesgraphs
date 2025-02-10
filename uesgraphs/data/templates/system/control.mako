  Modelica.Blocks.Sources.Constant dpSet(k=${dp_set})
    "Set pressure difference for substation" annotation (Placement(
        transformation(
        extent={{-10,-10},{10,10}},
        rotation=90,
        origin={92,-48})));
  Modelica.Blocks.Continuous.LimPID pControl(controllerType=Modelica.Blocks.Types.SimpleController.PI,
      %if k is not None:
      k = ${str(round(k, 0))},
      %endif
      %if Ti is not None:
      Ti = ${str(round(Ti, 0))},
      %endif
      yMax=${p_max},
      yMin=0,
      initType=Modelica.Blocks.Types.InitPID.InitialOutput,
    y_start=${p_max/2}) "Pressure controller" annotation (Placement(transformation(
        extent={{-10,10},{10,-10}},
        rotation=90,
        origin={92,-16})));
