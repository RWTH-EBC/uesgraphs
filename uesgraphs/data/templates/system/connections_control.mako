  connect(networkModel.dpOut, pControl.u_m) annotation (Line(points={{25,-10},{52,
          -10},{52,-16},{80,-16}}, color={0,0,127}));
  connect(dpSet.y, pControl.u_s)
    annotation (Line(points={{92,-37},{92,-28}}, color={0,0,127}));
  connect(pControl.y, networkModel.${name_supply}dpIn) annotation (Line(points={{92,
          -5},{62,-5},{62,-2},{30,-2}}, color={0,0,127}));
