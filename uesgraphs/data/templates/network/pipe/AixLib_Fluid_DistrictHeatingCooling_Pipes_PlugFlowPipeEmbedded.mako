  AixLib.Fluid.DistrictHeatingCooling.Pipes.PlugFlowPipeEmbedded pipe${str(name)}(
    redeclare package Medium = Medium,
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
    %if energyDynamics is not None:
    energyDynamics = ${str(round(energyDynamics, 4))},
    %endif
    %if use_zeta is not None:
    use_zeta = ${str(use_zeta).lower()},
    %endif
    %if from_dp is not None:
    from_dp = ${str(from_dp).lower()},
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
    roughness = ${str(round(roughness, 4))},
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
    initDelay = ${str(initDelay).lower()},
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
    %if sum_zetas is not None:
    sum_zetas = ${str(round(sum_zetas, 4))},
    %endif
    %if linearized is not None:
    linearized = ${str(linearized).lower()},
    %endif
    %if rho_soi is not None:
    rho_soi = ${str(round(rho_soi, 4))},
    %endif
    %if c is not None:
    c = ${str(round(c, 4))},
    %endif
    %if thickness_soi is not None:
    thickness_soi = ${str(round(thickness_soi, 4))},
    %endif
    %if lambda_ground is not None:
    lambda = ${str(round(lambda_ground, 4))},
    %endif
    %if d_in is not None:
    d_in = ${str(round(d_in, 4))},
    %endif
    %if nParallel is not None:
    nParallel = ${str(round(nParallel, 4))},
    %endif
    %if T0 is not None:
    T0 = ${str(round(T0, 4))},
    %endif
    %if _m_flow_start is not None:
    _m_flow_start = ${str(round(_m_flow_start, 4))},
    %endif
    %if _dp_start is not None:
    _dp_start = ${str(round(_dp_start, 4))},
    %endif
    %if show_T is not None:
    show_T = ${str(show_T).lower()},
    %endif
    %if allowFlowReversal is not None:
    allowFlowReversal = ${str(allowFlowReversal).lower()},
    %endif
    length = ${str(round(length, 4))},
    dIns = ${str(round(dIns, 4))},
    kIns = ${str(round(kIns, 4))}
    )
    annotation(Placement(transformation(
      extent={{-2,-2},{2,2}},
      rotation=0,
      origin={${str(round(x, 4))},${str(round(y, 4))}})));
<%def name="get_main_parameters()">
   length dIns kIns
</%def><%def name="get_aux_parameters()">
   CPip VEqu sta_default cp_default C rho_default energyDynamics use_zeta from_dp dh v_nominal ReC roughness m_flow_nominal m_flow_small cPip rhoPip thickness T_start_in T_start_out initDelay m_flow_start R fac sum_zetas linearized rho_soi c thickness_soi lambda_ground d_in nParallel T0 _m_flow_start _dp_start show_T allowFlowReversal
</%def><%def name="get_connector_names()">
   
</%def>