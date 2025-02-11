  Modelica.Blocks.Sources.CombiTimeTable TGroundTable(
    tableOnFile=true,
    tableName="T_ground",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://${name_model}/Resources/Inputs/T_ground.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=90,
      origin={20, -80}
    )));
