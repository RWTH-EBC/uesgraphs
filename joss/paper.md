---
title: 'UESgraphs: Automated graph-based district heating and cooling simulation model generation and analysis tool.'

tags:
  - Python
  - Modelica
  - District Heating and Cooling
  - Simulation
  - Analysis

authors:
  - name: Rahul M. Karuvingal
    orcid: 0009-0009-0165-0527
    affiliation: 1 
  - name: Kai Droste
    orcid: 0000-0002-3088-7138
    affiliation: 1
  - name: Leon Kopka
    orcid: 0009-0005-4125-8811
    affiliation: 1
  - name: Jonas Klingebiel
    orcid: 0000-0002-7489-0312
    affiliation: 1
  - name: Dirk Müller
    orcid: 0000-0002-6106-6607
    affiliation: 1

affiliations:
 - name: Institute for Energy Efficient Buildings and Indoor Climate, RWTH Aachen University
   index: 1

date: 12 October 2025

bibliography: paper.bib

---

# Summary

`UESgraphs` (Urban Energy Systems graphs) is a Python-based tool for automated generation and analysis of graph-based district heating and cooling (DHC) network simulation models. The package enables researchers and engineers to create detailed thermal network models from minimal input data, including building characteristics, connection topologies, and thermal demands. A key strength of `UESgraphs` is its flexible data integration capability, supporting diverse input formats including OpenStreetMap data, GIS files (GEOJSON, Shapefiles), DWG files, CityGML datasets, as well as CSV files and Python dictionaries. Using graph theory principles, `UESgraphs` automatically constructs network representations where nodes represent buildings, substations, and supply stations, while edges represent pipes with associated thermal and hydraulic properties. Key features include automated network topology simplification, hydronic sizing, automated Modelica model creation for thermo-hydraulic dynamic simulations, thermal loss calculations, and postprocessing of simulation results. Through its streamlined model development process, `UESgraphs` enables researchers and practitioners to perform rapid scenario analysis, system optimization, and informed decision-making in DHC network planning and operation.

# Statement of need

DHC networks are essential infrastructure for achieving climate neutrality by decarbonizing the building sector [@EU2023L1791]. However, planning and optimizing these networks requires complex thermo-hydraulic simulations that account for dynamic thermal losses, pressure drops, flow distributions, and temperature propagation through the network [@denarie_dynamical_2023]. Current simulation workflows present significant challenges that `UESgraphs` addresses through four key capabilities:

* **Automation** of DHC network model generation is critical for reducing development time and expertise barriers. Traditional approaches require manual creation of network topologies, pipe configurations, and component connections in simulation environments like Modelica/Dymola, consuming weeks of specialized effort and introducing errors [@Wetter_2014]. Existing tools either provide steady-state analyses lacking temporal dynamics, or demand extensive manual input for dynamic simulations [@Lund_2014]. `UESgraphs` automates the entire workflow from graph-based network topology to ready-to-simulate Modelica models, reducing development time from weeks to hours while ensuring consistency and reproducibility.

* **Integration** of graph theory with thermo-hydraulic simulation enables enhanced network analysis and optimization. By representing DHC networks as graphs, nodes denote components like buildings, substations, and supply stations, while edges represent pipes with thermal and hydraulic properties. This structure enables `UESgraphs` to generate simulation models and visualize simulation results directly within the graph framework. Additionally the framework is used for automatic topology simplification, pipe sizing, and network optimization. This graph-based approach facilitates rapid scenario comparison and design alternative evaluation, essential for evidence-based DHC planning [@Schweiger_2017].

* **Scalability** is a key requirement for resource-efficient transformation of the energy sector, as numerous existing districts require retrofitting and thousands of new DHC networks must be planned in the coming decades [@Persson_2014; @Connolly_2014]. `UESgraphs` enables users to efficiently generate models for networks of varying sizes and complexities, conduct comparative evaluations across multiple scenarios, and apply findings to a wide range of district typologies. By providing a modular, open-source framework, the tool supports the scientific community in addressing previously underserved multidisciplinary challenges in urban energy modeling [@Reinhart_2016].

* **Accessibility** to advanced DHC simulation capabilities democratizes their use among researchers, planners, and practitioners. The tool's Python-based architecture with minimal input requirements (building characteristics, connection topology, thermal demands) lowers the technical barrier for conducting detailed thermo-hydraulic analyses. Automated post-processing functions enable quick evaluation of simulation results, supporting iterative design processes and multi-criteria decision-making in DHC system planning and optimization studies.

# Functional principle 

`UESgraphs` operates through a modular workflow that transforms minimal network topology data into executable thermo-hydraulic simulation models. The tool follows a five-stage process (Figure \ref{fig:flowchart}) : network definition, graph construction, topology simplification, model generation, and post-processing analysis. The current implementation builds upon and extends previous work on automated DHC network model generation [@fuchs_automated_2017; @mans_development_2022], incorporating enhanced analysis capabilities, expanded input data interfaces, and includes post-processing features.

\begin{figure}[H]
\centering
\includegraphics[width=.9\linewidth]{UESgraphs_Graphical_Abstract.pdf}
\caption{Workflow of \texttt{UESgraphs} showing the five-stage process from network definition to post-processing analysis.}
\label{fig:flowchart}
\end{figure}

**Network Definition and Input Data**: Users provide basic network information through CSV files or Python dictionaries, specifying building locations, connection topology (graph edges), thermal demand profiles, and optional supply/return temperature requirements. The minimal input includes node coordinates, edge connections, and time-resolved heating or cooling demands for each building. Network components such as substations, generation units, and storage systems can be integrated through predefined templates. Rather than relying on a single data source, UESgraphs provides input interfaces for OpenStreetMap data, GIS formats (GEOJSON, Shapefiles), DWG files, and CityGML datasets.

**Graph-Based Network Representation**: The tool constructs a district graph using the NetworkX library [@hagberg_networkx_2008], where nodes represent buildings, heat sources, or network junctions, and edges represent pipe segments. Each edge stores thermal-hydraulic properties including pipe diameter, length, insulation thickness, and burial depth. The graph structure enables algorithmic network analysis, automatic detection of supply and return paths, and identification of critical network sections.

**Automated Hydronic Sizing and Topology Simplification**: `UESgraphs` extracts peak thermal demands from time-series data for each building given as input by the user, combining space heating and domestic hot water loads. The tool calculates required mass flow rates based on supply and return temperature differentials and determines corresponding flow velocities. Pipe diameters in UESgraphs are automatically selected from an integrated Isoplus manufacturer catalog, matching calculated flow requirements to standard pipe sizes so that flow velocities remain within user-specified thresholds [@Isoplus2024]. Additionally, users can add and customize other manufacturer catalogs within the tool’s source code to fit project-specific needs. Each pipe segment is assigned properties including diameter, insulation thickness, burial depth, and material specifications, which parametrize the pipe models for thermal loss calculations during simulation. Network topology can be simplified through algorithmic merging of series-connected pipes or removal of redundant junction nodes while preserving hydraulic equivalence.

**Modelica Model Generation**: The core functionality exports the optimized network as ready-to-simulate Modelica models compatible with the open-source AixLib library [@mueller_aixlib_2016]. Users can either create custom Modelica models for supply systems, substations, and pipes, or utilize default models from the AixLib library package. The tool converts these Modelica models into templates, which are then systematically assigned to buildings, pipes, and supply components respectively. `UESgraphs` generates a complete district-level Modelica model by instantiating these templates with parameters automatically derived from the graph structure stored in JSON format. Connection equations linking all components are automatically generated based on the network topology.

**Simulation and Post-Processing**: The generated Modelica models are simulated in Dymola, producing result files in MAT format that contain time-resolved data for all network components. `UESgraphs` provides post-processing functions by handling the result files to analyze simulation outcomes, including constraint verification, Key Performance Indicator (KPI) evaluation, temperature distribution analysis, pressure drop assessment, thermal loss quantification, and energy balance verification across the network. The tool offers visualization capabilities to present results effectively, featuring color-coded plots for network parameters, 3D visualization of spatial temperature distributions, and exploded views of network topology. These visualization features enable rapid identification of operational issues, performance bottlenecks, and optimization opportunities within the district heating or cooling system.




# Further development

Future versions of `UESgraphs` will expand capabilities to support broader DHC system analysis and design workflows. The tool will maintain an active Git repository with detailed documentation. This ensures robustness and community engagement. Planned enhancements include integrating automated demand estimation through TEASER [@remmen_teaser_2018] for building thermal load calculations. The tool will enable static simulation capabilities using pandapipes for rapid hydraulic analysis. Further development focuses on the fourth and fifth generation of validated DHC supply and substation models, which were developed for the Transurban.NRW living lab project [@TransUrbanNRW]. These will be integrated into the AixLib/Fluid/DistrictHeatingCooling package and will be directly accesible with the tool. OpenModelica support will be added as an alternative simulation platform. This increases accessibility for users without commercial software licenses. These developments aim to establish `UESgraphs` as a robust, open-source solution for DHC network planning through modelling and simulation.

# Acknowledgements

We gratefully acknowledge the financial support provided by the BMWE (Federal Ministry for Economic Affairs and Energy) and the European Union, grant number \textit{03EWR020E}.



# References

