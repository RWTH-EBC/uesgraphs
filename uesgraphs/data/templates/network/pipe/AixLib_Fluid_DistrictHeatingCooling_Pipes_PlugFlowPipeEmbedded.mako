  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe${str(name)}(
    redeclare package Medium = Medium,
    %if from_dp is not None:
    from_dp = ${str(round(from_dp, 4))},
    %endif
    %if dh is not None:
    dh = ${str(round(dh, 4))},
    %endif
    %if v_nominal is not None:
    v_nominal = ${str(round(v_nominal, 4))},
    %endif
    %if ReC is not None:
    ReC = ${str(round(ReC, 4))},
    %endif
    %if roughness is not None:
    roughness = ${str(roughness)},
    %endif
    %if m_flow_nominal is not None:
    m_flow_nominal = ${str(round(m_flow_nominal, 4))},
    %endif
    %if m_flow_small is not None:
    m_flow_small = ${str(round(m_flow_small, 4))},
    %endif
    %if cPip is not None:
    cPip = ${str(round(cPip, 4))},
    %endif
    %if rhoPip is not None:
    rhoPip = ${str(round(rhoPip, 4))},
    %endif
    %if thickness is not None:
    thickness = ${str(round(thickness, 4))},
    %endif
    %if T_start_in is not None:
    T_start_in = ${str(round(T_start_in, 4))},
    %endif
    %if T_start_out is not None:
    T_start_out = ${str(round(T_start_out, 4))},
    %endif
    %if initDelay is not None:
    initDelay = ${str(round(initDelay, 4))},
    %endif
    %if m_flow_start is not None:
    m_flow_start = ${str(round(m_flow_start, 4))},
    %endif
    %if R is not None:
    R = ${str(round(R, 4))},
    %endif
    %if fac is not None:
    fac = ${str(round(fac, 4))},
    %endif
    %if homotopyInitialization is not None:
    homotopyInitialization = ${str(round(homotopyInitialization, 4))},
    %endif
    %if linearized is not None:
    linearized = ${str(round(linearized, 4))},
    %endif
    %if CPip is not None:
    CPip = ${str(round(CPip, 4))},
    %endif
    %if VEqu is not None:
    VEqu = ${str(round(VEqu, 4))},
    %endif
    %if sta_default is not None:
    sta_default = ${str(round(sta_default, 4))},
    %endif
    %if cp_default is not None:
    cp_default = ${str(round(cp_default, 4))},
    %endif
    %if C is not None:
    C = ${str(round(C, 4))},
    %endif
    %if rho_default is not None:
    rho_default = ${str(round(rho_default, 4))},
    %endif
    %if allowFlowReversal is not None:
    allowFlowReversal = ${str(allowFlowReversal).replace("T","t").replace("F","f")},
    %endif
    %if rho is not None:
    rho = ${str(round(rho, 4))},
    %endif
    %if c is not None:
    c = ${str(round(c, 4))},
    %endif
    %if thickness_ground is not None:
    thickness_ground = ${str(round(thickness_ground, 4))},
    %endif
    %if lambda_ground is not None:
    lambda = ${str(round(lambda_ground, 4))},
    %endif
    length = ${str(round(length, 4))},
    dIns = ${str(round(dIns, 4))},
    kIns = ${str(round(kIns, 4))},
    nPorts = ${str(round(nPorts, 4))}
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      %if rotation is not None:
      rotation = ${str(round(rotation, 4))},
      %else:
      rotation = 0,
      %endif
      origin={${str(round(x, 4))},${str(round(y, 4))}})));
<%def name="get_main_parameters()">
   length dIns kIns nPorts
</%def><%def name="get_aux_parameters()">
   from_dp dh v_nominal ReC roughness m_flow_nominal m_flow_small cPip rhoPip thickness T_start_in T_start_out initDelay m_flow_start R fac homotopyInitialization linearized CPip VEqu sta_default cp_default C rho_default allowFlowReversal rho c thickness_ground lambda_ground
</%def><%def name="get_connector_names()">
   
</%def>