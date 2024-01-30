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
