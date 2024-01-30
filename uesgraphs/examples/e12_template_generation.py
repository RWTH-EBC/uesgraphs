from uesgraphs.systemmodels.templates import UESTemplates
import shapely.geometry as sg


def main():
    # Path to Aixlib library
    path_aixlib = r"path-to-your-Aixlib/AixLib/AixLib/package.mo"

    # Names of demand models
    demand_models = [
        "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDp",
        "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.HeatPumpCarnot",
        # "AixLib.Fluid.DistrictHeatingCooling.Demands.OpenLoop.VarTSupplyDpFixedTempDifferenceBypass",
    ]
    # create and test demand models
    for model_name in demand_models:
        template_gen = UESTemplates(model_name=model_name, model_type="Demand")
        template_gen.generate_new_template(path_library=path_aixlib)

        test_demand = {
            "name": "B1",
            "node_type": "building",
            "position": sg.Point(64.76, 217.14),
            "is_supply_heating": False,
            "is_supply_cooling": False,
            "is_supply_electricity": False,
            "is_supply_gas": False,
            "is_supply_other": False,
            "has_table": False,
            "dTDesign": 30,
            "dTBuilding": 10,
            "TSupplyBuilding": 70,
            "m_flow_nominal": 10,
            "m_flo_bypass": 0.5,    # for Bypass Template
            "Q_flow_nominal": 22719.1187448,
            "TReturn": 323.15,
            "_dp_start": 20,
            "comp_model": model_name,
        }

        template_gen = UESTemplates(model_name=test_demand["comp_model"], model_type="Demand")
        mo = template_gen.render(node_data=test_demand, i=1, number_of_instances=1)
        print(mo)

    # Names of Pipe models
    pipe_models = [
        "AixLib.Fluid.DistrictHeatingCooling.Pipes.StaticPipe",
        "AixLib.Fluid.FixedResistances.PlugFlowPipe",
        "AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeZeta",
    ]
    # create and test pipe models
    for model_name in pipe_models:
        template_gen = UESTemplates(model_name=model_name, model_type="Pipe")
        template_gen.generate_new_template(path_library=path_aixlib)

        test_pipe = {
            "name": "P1",
            "node_type": "pipe",
            "position": sg.Point(64.76, 217.14),
            "m_flow_nominal": 10,
            "length": 666,
            "dIns": 0.05,
            "kIns": 0.0032,
            "nPorts": 2,
            "comp_model": model_name,
        }
        template_gen = UESTemplates(model_name=test_pipe["comp_model"], model_type="Pipe")
        mo = template_gen.render(node_data=test_pipe, i=1, number_of_instances=1)
        print(mo)

    # Names of Supply models
    supply_models = [
        "AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceIdeal",
        "AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourcePower",
        "AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourcePowerDoubleMvar",
        "AixLib.Fluid.DistrictHeatingCooling.Supplies.OpenLoop.SourceSpeedControl",
    ]
    # create and test supply models
    for model_name in supply_models:
        template_gen = UESTemplates(model_name=model_name, model_type="Supply")
        template_gen.generate_new_template(path_library=path_aixlib)

        test_supply = {
            "name": "S1",
            "node_type": "building",
            "position": sg.Point(64.76, 217.14),
            "is_supply_heating": True,
            "is_supply_cooling": False,
            "is_supply_electricity": False,
            "is_supply_gas": False,
            "is_supply_other": False,
            "has_table": False,
            "pReturn": 20000,
            "TReturn": 293.15,
            "comp_model": model_name,
        }
        template_gen = UESTemplates(model_name=test_supply["comp_model"], model_type="Supply")
        mo = template_gen.render(node_data=test_supply, i=1, number_of_instances=1)
        print(mo)


if __name__ == "__main__":
    main()
