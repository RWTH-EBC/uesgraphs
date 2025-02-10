    experiment(
      Tolerance=${tolerance},
      StopTime=${stop_time},
      Interval=${interval},
      __Dymola_Algorithm="${solver}",
      __Dymola_experimentSetupOutput(events=false)
    )
