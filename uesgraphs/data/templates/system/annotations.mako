annotation (
  Documentation(
    info="<html>
    <p>System model connecting the network model with table inputs</p>
    </html>", revisions="<html>
    <ul>
      <li><i>${now.strftime("%B %d, %Y")}&nbsp;</i> uesmodels ${version}:<br/>Auto-generated.</li>
    </ul>
    </html>"
    ),
  uses(AixLib),
  experiment(
      Tolerance=${tolerance},
      StopTime=${stop_time},
      Interval=${interval},
      __Dymola_Algorithm="${solver}"),
      __Dymola_experimentSetupOutput(events=false)
);
