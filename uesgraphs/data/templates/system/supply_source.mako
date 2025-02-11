  Modelica.Blocks.Sources.CombiTimeTable ${name_supply + '_' + name_connector + '_Table'}(
    tableOnFile=true,
    tableName="${name_connector}",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://${name_model}/Resources/Inputs/supply_${name_supply + '_' + name_connector}.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=180,
      origin={${str(round(70+20*(number_of_input),0))}, ${str(round(80 - i*160/max((number_of_supplies-1), 1) - 10 * (number_of_input), 4))}}
    )));
