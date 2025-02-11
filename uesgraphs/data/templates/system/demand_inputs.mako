  Modelica.Blocks.Sources.CombiTimeTable ${name_demand + 'Table'}(
    tableOnFile=true,
    tableName="demand",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://${name_model}/Resources/Inputs/demand_${name_demand}_heat.txt"
    ),
    smoothness=Modelica.Blocks.Types.Smoothness.ContinuousDerivative,
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={-70, ${str(round(80 - i*160/(max(number_of_demands-1.0, 1.0)), 4))}}
    )));

