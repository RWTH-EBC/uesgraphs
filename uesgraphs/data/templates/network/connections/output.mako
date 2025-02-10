  Modelica.Blocks.Interfaces.RealOutput ${str(name)}(unit="${str(unit)}")
    "System Output"
  % if annotation:
    annotation(Placement(
      transformation(
        extent={{-2,-2},{2,2}},
        rotation=0,
        origin={{0, 0}}),
      iconTransformation(
        extent={{-2,-2},{2,2}},
        rotation=90,
        origin={50, -100})
      ));
  % else:
    ;
  % endif