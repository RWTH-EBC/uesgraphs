  connect(networkModel.${name_supply + name_connector}, ${name_supply + '_' + name_connector + '_Table'}.y[1])
    annotation (Line(
        points={
          {70, ${str(round(80 - i*160/max((number_of_supplies-1), 1), 4))}},{20, 0}
        },
        color={0,0,127}
      )
    );
