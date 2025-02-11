  Modelica.Blocks.Sources.CombiTimeTable dhwTable(
    tableOnFile=true,
    tableName="demand",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://${name_model}/Resources/Inputs/demand_dhw.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={-70, ${str(round(80 - i*160/(number_of_demands-1), 4))}}
    )));

