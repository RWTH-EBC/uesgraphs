  connect(networkModel.${name_demand + name_connector}, ${name_demand + 'Table'}.y[1])
    annotation (Line(
        points={
          {-70, ${str(round(80 - i*160/(max(number_of_demands-1.0, 1.0)), 4))}},{20, 0}
        },
        color={0,0,127}
      )
    );
