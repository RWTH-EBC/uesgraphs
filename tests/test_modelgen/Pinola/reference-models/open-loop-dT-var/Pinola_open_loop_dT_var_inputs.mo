model Pinola_open_loop_dT_var_inputs
  "System model with inputs for network"
  extends Modelica.Icons.Example;

  Pinola_open_loop_dT_var networkModel
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={20, 0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable B1Table(
    tableOnFile=true,
    tableName="demand",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Pinola_open_loop_dT_var/Resources/Inputs/demand_B1_heat.txt"
    ),
    smoothness=Modelica.Blocks.Types.Smoothness.ContinuousDerivative,
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={-70, 80.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable B2Table(
    tableOnFile=true,
    tableName="demand",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Pinola_open_loop_dT_var/Resources/Inputs/demand_B2_heat.txt"
    ),
    smoothness=Modelica.Blocks.Types.Smoothness.ContinuousDerivative,
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={-70, 0.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable B3Table(
    tableOnFile=true,
    tableName="demand",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Pinola_open_loop_dT_var/Resources/Inputs/demand_B3_heat.txt"
    ),
    smoothness=Modelica.Blocks.Types.Smoothness.ContinuousDerivative,
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={-70, -80.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable S1_TIn_Table(
    tableOnFile=true,
    tableName="TIn",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Pinola_open_loop_dT_var/Resources/Inputs/supply_S1_TIn.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=180,
      origin={70, 80.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable S1_dpIn_Table(
    tableOnFile=true,
    tableName="dpIn",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Pinola_open_loop_dT_var/Resources/Inputs/supply_S1_dpIn.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=180,
      origin={90, 70.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable S2_TIn_Table(
    tableOnFile=true,
    tableName="TIn",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Pinola_open_loop_dT_var/Resources/Inputs/supply_S2_TIn.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=180,
      origin={70, -80.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable S2_dpIn_Table(
    tableOnFile=true,
    tableName="dpIn",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Pinola_open_loop_dT_var/Resources/Inputs/supply_S2_dpIn.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=180,
      origin={90, -90.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable TGroundTable(
    tableOnFile=true,
    tableName="T_ground",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Pinola_open_loop_dT_var/Resources/Inputs/T_ground.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=90,
      origin={20, -80}
    )));
equation
  connect(networkModel.B1Q_flow_input, B1Table.y[1])
    annotation (Line(
        points={
          {-70, 80.0},{20, 0}
        },
        color={0,0,127}
      )
    );
  connect(networkModel.B2Q_flow_input, B2Table.y[1])
    annotation (Line(
        points={
          {-70, 0.0},{20, 0}
        },
        color={0,0,127}
      )
    );
  connect(networkModel.B3Q_flow_input, B3Table.y[1])
    annotation (Line(
        points={
          {-70, -80.0},{20, 0}
        },
        color={0,0,127}
      )
    );
  connect(networkModel.S1TIn, S1_TIn_Table.y[1])
    annotation (Line(
        points={
          {70, 80.0},{20, 0}
        },
        color={0,0,127}
      )
    );

  connect(networkModel.S1dpIn, S1_dpIn_Table.y[1])
    annotation (Line(
        points={
          {70, 80.0},{20, 0}
        },
        color={0,0,127}
      )
    );

  connect(networkModel.S2TIn, S2_TIn_Table.y[1])
    annotation (Line(
        points={
          {70, -80.0},{20, 0}
        },
        color={0,0,127}
      )
    );

  connect(networkModel.S2dpIn, S2_dpIn_Table.y[1])
    annotation (Line(
        points={
          {70, -80.0},{20, 0}
        },
        color={0,0,127}
      )
    );

  connect(networkModel.TGroundIn, TGroundTable.y[1])
    annotation (Line(
        points={
          {20, -80},{20, 0}
        },
        color={0,0,127}
      )
    );
annotation (
  Documentation(
    info="<html>
    <p>System model connecting the network model with table inputs</p>
    </html>", revisions="<html>
    <ul>
      <li><i>January 09, 2020&nbsp;</i> uesmodels 0.8.3:<br/>Auto-generated.</li>
    </ul>
    </html>"
    ),
  uses(AixLib),
  experiment(
      Tolerance=1e-05,
      StopTime=603900,
      Interval=900,
      __Dymola_Algorithm="Cvode"),
      __Dymola_experimentSetupOutput(events=false)
);
end Pinola_open_loop_dT_var_inputs;
