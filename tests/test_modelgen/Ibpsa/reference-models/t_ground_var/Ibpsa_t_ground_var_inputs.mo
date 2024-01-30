model Ibpsa_t_ground_var_inputs
  "System model with inputs for network"
  extends Modelica.Icons.Example;

  Ibpsa_t_ground_var networkModel
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={20, 0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable point_2Table(
    tableOnFile=true,
    tableName="demand",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Ibpsa_t_ground_var/Resources/Inputs/demand_point_2_heat.txt"
    ),
    smoothness=Modelica.Blocks.Types.Smoothness.ContinuousDerivative,
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={-70, 80.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable point_3Table(
    tableOnFile=true,
    tableName="demand",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Ibpsa_t_ground_var/Resources/Inputs/demand_point_3_heat.txt"
    ),
    smoothness=Modelica.Blocks.Types.Smoothness.ContinuousDerivative,
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={-70, 0.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable point_4Table(
    tableOnFile=true,
    tableName="demand",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Ibpsa_t_ground_var/Resources/Inputs/demand_point_4_heat.txt"
    ),
    smoothness=Modelica.Blocks.Types.Smoothness.ContinuousDerivative,
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={-70, -80.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable supply_TIn_Table(
    tableOnFile=true,
    tableName="TIn",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Ibpsa_t_ground_var/Resources/Inputs/supply_supply_TIn.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=180,
      origin={70, 80.0}
    )));

  Modelica.Blocks.Sources.CombiTimeTable supply_dpIn_Table(
    tableOnFile=true,
    tableName="dpIn",
    columns={2},
    fileName=Modelica.Utilities.Files.loadResource(
      "modelica://Ibpsa_t_ground_var/Resources/Inputs/supply_supply_dpIn.txt"
    ),
    extrapolation=Modelica.Blocks.Types.Extrapolation.Periodic)
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=180,
      origin={90, 70.0}
    )));

  AixLib.BoundaryConditions.GroundTemperature.GroundTemperatureKusuda TGroundKusuda(
    t_shift=3,
    alpha=0.04,
    D=1,
    T_mean=283.6,
    T_amp=19.25
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
equation
  connect(networkModel.point_2Q_flow_input, point_2Table.y[1])
    annotation (Line(
        points={
          {-70, 80.0},{20, 0}
        },
        color={0,0,127}
      )
    );
  connect(networkModel.point_3Q_flow_input, point_3Table.y[1])
    annotation (Line(
        points={
          {-70, 0.0},{20, 0}
        },
        color={0,0,127}
      )
    );
  connect(networkModel.point_4Q_flow_input, point_4Table.y[1])
    annotation (Line(
        points={
          {-70, -80.0},{20, 0}
        },
        color={0,0,127}
      )
    );
  connect(networkModel.supplyTIn, supply_TIn_Table.y[1])
    annotation (Line(
        points={
          {70, 80.0},{20, 0}
        },
        color={0,0,127}
      )
    );

  connect(networkModel.supplydpIn, supply_dpIn_Table.y[1])
    annotation (Line(
        points={
          {70, 80.0},{20, 0}
        },
        color={0,0,127}
      )
    );

  connect(TGroundKusuda.port_a, TGroundIn.port)
    annotation (Line(
        points={
          {20, -80}, {20, -50}
        },
        color={191,0,0}
      )
    );

  connect(TGroundIn.T, networkModel.TGroundIn)
    annotation (Line(
        points={
          {20, -50},{20, 0}
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
end Ibpsa_t_ground_var_inputs;
