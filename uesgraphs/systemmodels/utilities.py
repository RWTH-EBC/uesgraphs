"""This module collects utilities and convenience functions for model generation"""

from uesgraphs.systemmodels import systemmodelheating as sysmh

import networkx as nx

def prepare_graph(
    graph,
    T_supply,
    p_supply,
    T_return,
    p_return,
    dT_design,
    m_flow_nominal=None,
    dp_nominal=None,
    dT_building=None,
    T_supply_building=None,
    cop_nominal=None,
    T_con_nominal=None,
    T_eva_nominal=None,
    dTEva_nominal=None,
    dTCon_nominal=None
):
    """Adds data for model generation to the uesgraph

    Parameters
    ----------
    graph : uesgraphs.uesgraph.UESGraph
        Network graph with all data for the model
    T_supply : list
        Design supply temperature in K
    p_supply : float
        Prescribed supply pressure in Pa
    T_return : float
        Design return temperature in K
    p_return : float
        Prescribed return pressure in Pa
    dT_design : float
        Design temperature difference over substation in K
    m_flow_nominal : float
        Nominal mass flow rate in kg/s
    dp_nominal : float
        Nominal pressure drop over the substation in Pa
    dT_building : float
        Prescribed temperature difference for the building heating system in K
    T_supply_building : float
        Supply temperature of the building heating system in K
    cop_nominal : float
        A nominal COP for substations that use a heat pump
    T_con_nominal : float
        Nominal condenser temperature of heat pump
    T_eva_nominal : float
        Nominal evaporator temperature of heat pump
    dTEva_nominal : float (default -10 K)
        Nominal temperature difference at heat pump evaporator
    dTCon_nominal : float (default 10 K)
        Nominal temperature difference at heat pump condenser
    """
    for node in graph.nodelist_building:
        is_supply = "is_supply_{}".format(graph.graph["network_type"])
        if graph.nodes[node][is_supply]:
            # TODO decision about variable naming
            # graph.nodes[node]['T_supply'] = T_supply
            # graph.nodes[node]['p_supply'] = [p_supply]
            # graph.nodes[node]['p_return'] = p_return
            graph.nodes[node]["TIn"] = T_supply
            graph.nodes[node]["dpIn"] = [p_supply]
            graph.nodes[node]["pReturn"] = p_return
        else:
            input_heat = graph.nodes[node]["input_heat"]
            try:
                input_dhw = graph.nodes[node]["input_dhw"]
                input_cool = graph.nodes[node]["input_cool"]
            except:
                input_dhw = [0]
                input_cool = [0]
            graph.nodes[node]["Q_flow_nominal"] = max(
                max(input_heat),
                max(input_dhw),
                max(input_cool))
            if dp_nominal is not None:
                graph.nodes[node]["dp_nominal"] = dp_nominal
            # graph.nodes[node]['dT_design'] = dT_design
            graph.nodes[node]["dTDesign"] = dT_design
            if dT_building is not None:
                # graph.nodes[node]['dT_building'] = dT_building
                graph.nodes[node]["dTBuilding"] = dT_building
            if T_supply_building is not None:
                # graph.nodes[node]['T_supply_building'] = T_supply_building
                graph.nodes[node]["TSupplyBuilding"] = T_supply_building
            if cop_nominal is not None:
                graph.nodes[node]["cop_nominal"] = cop_nominal
            if T_con_nominal is not None:
                graph.nodes[node]["T_con_nominal"] = T_con_nominal
            if T_eva_nominal is not None:
                graph.nodes[node]["T_eva_nominal"] = T_eva_nominal
            if dTEva_nominal is not None:
                graph.nodes[node]["dTEva_nominal"] = dTEva_nominal
            if dTCon_nominal is not None:
                graph.nodes[node]["dTCon_nominal"] = dTCon_nominal
        # graph.nodes[node]['T_return'] = T_return
        graph.nodes[node]["TReturn"] = T_return

    if m_flow_nominal is not None:
        for edge in graph.edges():
            graph.edges[edge[0], edge[1]]["m_flow_nominal"] = m_flow_nominal

    return graph


def create_model(
    name,
    save_at,
    graph,
    stop_time,
    timestep,
    model_supply,
    model_demand,
    model_pipe,
    model_medium,
    model_ground,
    T_nominal,
    p_nominal,
    solver=None,
    tolerance=1e-5,
    params_kusuda=None,
    fraction_glycol=None,
    pressure_control_supply=None,
    pressure_control_dp=None,
    pressure_control_building=None,
    pressure_control_p_max=None,
    pressure_control_k=None,
    pressure_control_ti=None,
    t_ground_prescribed=None,
    short_pipes_static=None,
    meta_data=None
):
    """Generic model generation for setup defined through the parameters

    Parameters
    ----------
    name : str
        Name of the model (First character will be capitalized, cannot start with digit)
    save_at : str
        Directory where to store the generated model package
    graph : uesgraphs.uesgraph.UESGraph
        Network graph with all necessary data for model generation
    stop_time : int
        Stop time of the simulation in seconds
    timestep : int
        Timestep of the simulation in seconds
    model_supply : str
        One of the supply models supported by uesmodels
    model_demand : str
        One of the demand models supported by uesmodels
    model_pipe : str
        One of the pipe models supported by uesmodels
    model_medium : str
        One of the medium models supported by uesmodels
    model_ground : str
        One of the ground models supported by uesmodels
    T_nominal : float
        Nominal temperature for model initialization in K
    p_nominal : float
        Nominal pressure for model initialization in Pa
    solver : str
        Solver to use in dymola
    tolerance : float
        Solver tolerance to store in the model
    params_kusuda : dict
        Kusuda ground model parameters. Default values are for Aachen taken from TRY file
    fraction_glycol : float
        Value between 0 (100 % water) and 0.6 (60 % glycol) for the medium in the network
    pressure_control_supply : str
        Name of supply to control the pressure in the network
    pressure_control_dp : float
        Pressure difference to be held at reference building
    pressure_control_building : str
        Name of the reference building for the network. For default
        `'max_distance'`, the building with the greatest distance from the
        supply unit will be chosen
    pressure_control_p_max : float
        Maximum pressure allowed for the pressure controller
    pressure_control_k : int
        gain of controller
    pressure_control_ti : int
        time constant for integrator block
    t_ground_prescribed : list
        List of ground temperatures for every time step when using `model_ground="t_ground_table"`
    short_pipes_static : float
        The float value specifies the length of pipes considered short. If a pipe length is smaller
        than the value for `short_pipes_static`, a static pipe model will be used for it.
    meta_data : dict
        Dictionary with meta data
    """
    assert not name[0].isdigit(), "Model name cannot start with a digit"

    if params_kusuda is None:
        params_kusuda = {
            "T_mean": 273.15 + 10.45,
            "T_amp": 38.5 / 2,
            "t_shift": 3,
            "alpha": 0.04,
            "D": 1,
        }

    new_model = sysmh.SystemModelHeating(network_type=graph.graph["network_type"])
    new_model.stop_time = stop_time
    new_model.timestep = timestep
    new_model.import_from_uesgraph(graph)
    new_model.set_connection(remove_network_nodes=True)

    if solver:
        new_model.solver = solver

    new_model.add_return_network = True
    new_model.medium = model_medium
    new_model.T_nominal = T_nominal
    new_model.p_nominal = p_nominal

    if pressure_control_supply is not None:
        msg = "All or none of the pressure_control variables must be set"
        assert pressure_control_dp is not None, msg
        assert pressure_control_building is not None, msg
        assert pressure_control_p_max is not None, msg
        new_model.set_control_pressure(
            name_supply=pressure_control_supply,
            dp=pressure_control_dp,
            name_building=pressure_control_building,
            p_max=pressure_control_p_max,
            k=pressure_control_k,
            ti=pressure_control_ti
        )

    if fraction_glycol is not None:
        msg = "The medium model for glycol only supports fractions of glycol between 0.0 and 0.6"
        assert fraction_glycol >= 0 and fraction_glycol <= 0.6, msg
        new_model.fraction_glycol = fraction_glycol

    if model_ground == "t_ground_table":
        new_model.ground_model = "t_ground_table"
    elif model_ground == "t_ground_kusuda":
        new_model.ground_model = "t_ground_kusuda"
        new_model.params_kusuda = params_kusuda

    if t_ground_prescribed is not None:
        new_model.graph["T_ground"] = t_ground_prescribed

    new_model.tolerance = tolerance

    for node in new_model.nodelist_building:
        is_supply = "is_supply_{}".format(new_model.network_type)
        if new_model.nodes[node][is_supply]:
            new_model.nodes[node]["comp_model"] = model_supply
        else:
            new_model.nodes[node]["comp_model"] = model_demand

    for node in new_model.nodelist_pipe:
        new_model.nodes[node]["comp_model"] = model_pipe
        if short_pipes_static is not None:
            length = new_model.nodes[node]["length"]
            if length < short_pipes_static:
                new_model.nodes[node][
                    "comp_model"
                ] = "AixLib.Fluid.DistrictHeatingCooling.Pipes.StaticPipe"

    name = name[0].upper() + name[1:]
    new_model.model_name = name
    new_model.meta_data = meta_data
    new_model.write_modelica_package(save_at=save_at)


def estimate_fac(graph, u_form_distance=25, n_gate_valve=2.0):
    """Calculate fac for all pipes based on m_flow_nominal

    Parameters
    ----------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    u_form_distance : int
        distance between U-form for thermal stress of pipes. Default: every 25m one U-Form is added
    n_gate_valve : float
        number of gate valves per pipe. For average values, n_gate_valve is a float. Default: 2 Gate valves per pipe.
    Returns
    -------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    """

    for edge in graph.edges():
        d = graph.edges[edge]["diameter"]
        l = graph.edges[edge]["length"]

        # guess equivalent length
        # Data taken from https://neutrium.net/fluid_flow/pressure-loss-from-fittings-equivalent-length-method/

        # Approx. every 25 m a U-form for thermal pressure is installed
        # U-form equals four 90° elbow fittings
        l_thermal_U_form = round(l / u_form_distance, 0) * 20 * 4

        # Every pipe is connected at both ends with a tee run-through
        l_tee_junction = 2 * 20

        # Every pipe has n_gate_valve Gate valves installed
        l_gate_valve = n_gate_valve * 8

        l_eq = l_thermal_U_form + l_tee_junction + l_gate_valve
        # factor accounts for theoretical additional length because of pressure drop by fittings
        fac = 1 + l_eq * d / l

        graph.edges[edge]["fac"] = fac

    return graph


def estimate_m_flow_nominal(graph, dT_design, network_type, cp=4184):
    """Calculate all design mass flows based on nominal loads for each edge

    Parameters
    ----------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    dT_design : float
        Design temperature difference between supply and return in K
    network_type : str
        {'heating', 'cooling'}
    cp : float
        Specific heat capacity of fluid in the network

    Returns
    -------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    """
    # Distinguish between supply and demand nodes
    demands = []
    supplies = []
    for node in graph.nodelist_building:
        if not graph.nodes[node]["is_supply_{}".format(network_type)]:
            demands.append(node)
        else:
            supplies.append(node)

    # Add loads of each building to each edge by following the shortest paths for each supply
    for supply in supplies:
        for node in demands:
            if nx.has_path(graph, supply, node):
                loads = [abs(x) for x in graph.nodes[node]["input_heat"]]
                load = max(loads)
                path = nx.shortest_path(graph, supply, node)
                for i, n in enumerate(path):
                    if n != path[-1]:
                        if (
                            "load_nominal_{}".format(supply)
                            not in graph.edges[path[i], path[i + 1]]
                        ):
                            graph.edges[path[i], path[i + 1]][
                                "load_nominal_{}".format(supply)
                            ] = load
                            graph.edges[path[i], path[i + 1]]["load_nominal"] = None
                        else:
                            graph.edges[path[i], path[i + 1]][
                                "load_nominal_{}".format(supply)
                            ] += load
                            graph.edges[path[i], path[i + 1]]["load_nominal"] = None

    # For multiple supplies, take maximum load for each edge
    for edge in graph.edges():
        if "load_nominal" in graph.edges[edge]:
            loads_nominal = []
            for supply in supplies:
                if "load_nominal_{}".format(supply) in graph.edges[edge]:
                    loads_nominal.append(
                        graph.edges[edge]["load_nominal_{}".format(supply)]
                    )
                    del graph.edges[edge]["load_nominal_{}".format(supply)]
            graph.edges[edge]["load_nominal"] = max(loads_nominal)

    # Calculate each edge's design mass flow rate based on load and dT_design
    for edge in graph.edges():
        if "load_nominal" in graph.edges[edge]:
            load = graph.edges[edge[0], edge[1]]["load_nominal"]
            m_flow_nominal = load / (cp * dT_design)
            graph.edges[edge[0], edge[1]]["m_flow_nominal"] = m_flow_nominal

    return graph


def estimate_m_flow_nominal_tablebased(graph, network_type):
    """Calculate m_flow_nominal based on the pipe diameter.

    This function calculates the m_flow_nominal based on the pipe diameter
    and according to the isoplus table for suggested m_flows for specific pipe
    diameters with a average pressure loss of 70 Pa/m. Link: 
    http://www.isoplus.de/fileadmin/user_upload/downloads/documents/germany/Catalogue_German/Kapitel_2_Starre_Verbundsysteme.pdf
    page 9

    Parameters
    ----------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    network_type : str
        {'heating', 'cooling'}

    Returns
    -------
    graph : uesgraphs.uesgraph.UESGraph
        Graph of the network
    """
    # As this function wants to estimate the nominal massflow based on the diameter,
    # the key is the diameter, the value is the nominal massflow
    # {
    #  key: value,
    #  diameter [mm]: m_flow_nominal [kg/s]
    # }
    pipe_dict = {
        21.7: 0.125,
        27.3: 0.25,
        36: 0.513888889,
        41.9: 0.763888889,
        53.9: 1.416666667,
        69.7: 2.819444444,
        82.5: 4.305555556,
        107.1: 8.541666667,
        132.5: 15,
        160.3: 24.58333333,
        210.1: 50,
        263: 90,
        312.7: 141.5277778,
        344.4: 182.6388889,
        393.8: 258.6111111,
        444.6: 354.1666667,
        495.4: 470.8333333,
        595.8: 755.5555556,
        695: 1130.555556,
        795.4: 1615.277778,
        894: 2347.222222,
        994: 2555.555556,
    }

    # min(enumerate(a), key=lambda x: abs(x[1]-11.5))

    for edge in graph.edges():
        diameter = graph.edges[edge]["diameter"]
        m_flow_nominal = pipe_dict[
            min(pipe_dict, key=lambda x: abs(x - diameter * 1000))
        ]
        graph.edges[edge[0], edge[1]]["m_flow_nominal"] = m_flow_nominal

    return graph
