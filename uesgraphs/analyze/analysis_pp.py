"""
Pandapipes analysis functions
================================================

Analyzes 

Author: Arkadi B.
Date: 2025-03-05
"""

from pathlib import Path

# Imports
import uesgraphs as ug
import numpy as np
from uesgraphs.utilities import set_up_file_logger
import matplotlib.pyplot as plt
import json
import copy
import pandas as pd
import os 

# ============================================================================
# ANALYSIS functions
# ============================================================================

class analysis_pp:
    """Class to perform various analyses on pandapipes UESGraphs"""
    def __init__(self, root_path: Path, timestep_hours: float = 1.0):
        self.root_path = root_path

        self.graph_supply_json = root_path / "uesgraphs.json"
        self.graph_return_json = root_path / "uesgraphs_return.json"

        self.timestep = timestep_hours


    def thermal_loss_analysis(self):
        """Thermal loss analysis for the sum over all pipes in the system"""
        logger = set_up_file_logger("thermal_loss_analysis", level=20)

        logger.info("=" * 80)
        logger.info("Thermal loss Analysis")
        logger.info("=" * 80)

        logger.info(f"Analyzing: {self.root_path}")
        logger.info(f"Supply Side UESGraph: {self.graph_supply_json}")
        logger.info(f"Return Side UESGraph: {self.graph_return_json}")

        # Load UESGraph
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: LOAD SUPPLY and RETURN NETWORK")
        logger.info("=" * 80)

        logger.info(f"Loading from JSON: {self.graph_supply_json}")
        graph = ug.UESGraph()
        graph.from_json(path=str(self.graph_supply_json), network_type="heating")
        logger.info(f"Loaded {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        
        logger.info(f"Loading from JSON: {self.graph_return_json}")
        graph_return = ug.UESGraph()
        graph_return.from_json(path=str(self.graph_return_json), network_type="heating")
        logger.info(f"Loaded {len(graph_return.nodes)} nodes, {len(graph_return.edges)} edges")

        # Add Q_loss from simulation data (should already be in edges if assigned correctly)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: ADD Q_LOSS FOR SYSTEM LOSSES")
        logger.info("=" * 80)
        system_loss_series = None

        for edge in graph.edges():
            edge_data = graph.edges[edge]
            edge_data_R = graph_return.edges[edge]

            Q_loss_two_pipes = np.array(edge_data["Q_loss"]) + np.array(edge_data_R["Q_loss"])

            if system_loss_series is None:
                system_loss_series = Q_loss_two_pipes.copy()
            else:
                system_loss_series += Q_loss_two_pipes

        # ------------------------------------------------------------------
        # SYSTEM TOTAL
        # ------------------------------------------------------------------
        if system_loss_series is not None:

            system_peak_loss = system_loss_series.max() / 1e3  # kW
            system_annual_loss = system_loss_series.sum() * self.timestep / 1e3

            print("\n" + "-" * 60)
            print("TOTAL PIPE HEAT LOSSES")
            print(f" Maximum Heat Loss over all pipes: {system_peak_loss:.2f} kW at timestep {system_loss_series.argmax()}")
            print(f"  Annual Heat Loss: {system_annual_loss:.3f} kWh")

    def pump_power_analysis(self, eta_total: float = 0.65):
        """Pump power analysis for the supply pumps in the system, based on mass flow and pressure drop data from the simulation
        
        Parameters:
        
        eta_total : float Default 0.65, can be set as required to reflect pump efficiency

        """
        logger = set_up_file_logger("pump_power_analysis", level=20)

        logger.info("=" * 80)
        logger.info("Pump power analysis")
        logger.info("=" * 80)

        logger.info(f"Analyzing: {self.root_path}")
        logger.info(f"Supply Side UESGraph: {self.graph_supply_json}")

        # Load UESGraph
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: LOAD SUPPLY NETWORK")
        logger.info("=" * 80)

        logger.info(f"Loading from JSON: {self.graph_supply_json}")
        graph = ug.UESGraph()
        graph.from_json(path=str(self.graph_supply_json), network_type="heating")
        logger.info(f"Loaded {len(graph.nodes)} nodes, {len(graph.edges)} edges")

        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: CALCULATE CENTRAL PUMP POWER")
        logger.info("=" * 80)

        for node_id, attrs in graph.nodes(data=True):

            if not attrs.get("is_supply_heating"):
                continue

            connected_edges = list(graph.edges(node_id, data=True))

            if not connected_edges:
                logger.warning(f"No connected edges for supply {node_id}")
                continue

            supply_mflow = None

            for u, v, e_attrs in connected_edges:

                if "m_flow" not in e_attrs:
                    continue
                
                logger.info(f"Found m_flow for edge ({u}, {v}) connected to supply {node_id}")
                m_flow_series = np.array(e_attrs["m_flow"])

                supply_mflow = abs(np.array(m_flow_series))

            if supply_mflow is None:
                logger.warning(f"No usable m_flow found for {node_id}")
                continue

            dp_flow_bar = attrs.get("dpFlow", 0.0)
            dp_flow = dp_flow_bar * 100000  # bar → Pa

            rho = attrs["rho"]

            Pel = (supply_mflow * dp_flow) / (rho * eta_total)  # Watt

            max_power = Pel.max()
            annual_energy_kWh = Pel.sum() * self.timestep / 1e3

            print(f"\nSupply Pump: {node_id}")
            print(f"  Max Power: {max_power:.2f} W at timestep {Pel.argmax()}")
            print(f"  Annual Energy: {annual_energy_kWh:.3f} kWh")

    def pipe_plots(self):
        logger = set_up_file_logger("graph_analysis", level=20)

        logger.info("="*60)
        logger.info("Graph ANALYSIS (Config-Based)")
        logger.info("="*60)

        logger.info(f"Analyzing: {self.root_path}")
        logger.info(f"Supply Side UESGraph: {self.graph_supply_json}")

        # Load UESGraph
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: LOAD SUPPLY NETWORK")
        logger.info("=" * 80)

        logger.info(f"Loading from JSON: {self.graph_supply_json}")
        graph = ug.UESGraph()
        graph.from_json(path=str(self.graph_supply_json), network_type="heating")
        logger.info(f"Loaded {len(graph.nodes)} nodes, {len(graph.edges)} edges")

        logger.info(f"Loading from JSON: {self.graph_return_json}")
        graph_return = ug.UESGraph()
        graph_return.from_json(path=str(self.graph_return_json), network_type="heating")
        logger.info(f"Loaded {len(graph_return.nodes)} nodes, {len(graph_return.edges)} edges")

        """Note: This is only used if you want to check the physical consistency of the results by comparing pipe temperatures to ground temperatures."""
        #ground_temp_df = pd.read_csv(self.root_path / "ground_temps_hassel.csv", index_col=0, parse_dates=True)
        #T_ground = ground_temp_df["1.0 m"].tolist()
        T_ground = None

        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: PLOT PIPE PLOTS")
        logger.info("=" * 80)

        output_dir = self.root_path / "analysis_outputs" / "pipe_plots"
        output_dir.mkdir(parents=True, exist_ok=True)

        for edge in graph.edges:
            edge_data = graph.edges[edge]
            temp_in_list = np.array(edge_data.get("T_in", None))
            temp_out_list = np.array(edge_data.get("T_out", None)) 
            edge_data_R = graph_return.edges[edge]
            temp_in_R_list = np.array(edge_data_R.get("T_in", None))
            temp_out_R_list = np.array(edge_data_R.get("T_out", None))

            T_in = edge_data_R.get("T_in")
            T_out = edge_data_R.get("T_out")

            """Note: This is only used if you want to check the physical consistency of the results 
                by comparing pipe temperatures to ground temperatures."""
            if T_ground is not None:
                T_in_arr = np.array(T_in)
                T_out_arr = np.array(T_out)
                Tamb = np.array(T_ground[:len(T_in_arr)])

                mask_problem = (T_out_arr - T_in_arr) > 0.1

                if mask_problem.any():
                    idx = np.where(mask_problem)[0][:5]
                    logger.warning(f"\nEdge {edge_data_R.get('pipeID')} hat T_out > T_in!")
                    logger.warning(f"Indices: {idx}")
                    logger.warning(f"T_in: {T_in_arr[idx]}")
                    logger.warning(f"T_out: {T_out_arr[idx]}")
                    logger.warning(f"T_amb: {Tamb[idx]}")

                    if (Tamb[idx] > T_in_arr[idx]).all():
                        logger.warning("Physikalisch OK (Umgebung wärmer)")
                    else:
                        logger.error("UNPHYSIKALISCH! Check deine Simulation!")

            if edge_data.get("T_in") is not None and edge_data.get("T_out") is not None:
                plt.figure(figsize=(14, 5))
                plt.plot(temp_in_list - temp_out_list, label="dT")
                plt.xlabel("Index")
                plt.ylabel("Temperature in °C")
                plt.title(f"PipeID {edge_data.get('pipeID', None)} Temperatures")
                plt.legend()
                plt.tight_layout()
                plt.grid(True)
                plt.savefig(output_dir/ f"pipe_temp_df_{edge_data.get('pipeID', None)}.png", dpi=300)
                plt.close()

            m_flow_from_list = edge_data.get("m_flow", None)
            if m_flow_from_list != None:
                plt.figure(figsize=(14, 5))
                plt.plot(m_flow_from_list, label="m_flow")
                plt.xlabel("Date")
                plt.ylabel("Mass flow in kg/s")
                plt.title(f"PipeID {edge_data.get('pipeID', None)} Mass flow")
                plt.legend()
                plt.tight_layout()
                plt.grid(True)
                plt.savefig(output_dir/ f"pipe_m_flow_{edge_data.get('pipeID', None)}.png", dpi=300)
                plt.close()

            Q_loss_list = edge_data.get("Q_loss", None)
            if Q_loss_list != None:
                plt.figure(figsize=(14, 5))
                plt.plot(Q_loss_list, label="Q_loss")
                plt.xlabel("Date")
                plt.ylabel("Thermal losses in W")
                plt.title(f"PipeID {edge_data.get('pipeID', None)} Themal loss")
                plt.legend()
                plt.tight_layout()
                plt.grid(True)
                plt.savefig(output_dir/ f"pipe_Q_loss_{edge_data.get('pipeID', None)}.png", dpi=300)
                plt.close()

            if edge_data_R.get("T_in") is not None and edge_data_R.get("T_out") is not None:
                plt.figure(figsize=(14, 5))
                plt.plot(temp_in_R_list - temp_out_R_list, label="dT")
                plt.xlabel("Index")
                plt.ylabel("Temperature in °C")
                plt.title(f"PipeID {edge_data.get('pipeID', None)} Temperatures")
                plt.legend()
                plt.tight_layout()
                plt.grid(True)
                plt.savefig(output_dir/ f"R_pipe_temp_df_{edge_data.get('pipeID', None)}.png", dpi=300)
                plt.close()

            m_flow_from_list = edge_data_R.get("m_flow", None)
            if m_flow_from_list != None:
                plt.figure(figsize=(14, 5))
                plt.plot(m_flow_from_list, label="m_flow")
                plt.xlabel("Date")
                plt.ylabel("Mass flow in kg/s")
                plt.title(f"PipeID {edge_data_R.get('pipeID', None)} Mass flow")
                plt.legend()
                plt.tight_layout()
                plt.grid(True)
                plt.savefig(output_dir/ f"R_pipe_m_flow_{edge_data_R.get('pipeID', None)}.png", dpi=300)
                plt.close()

            Q_loss_list = edge_data_R.get("Q_loss", None)
            if Q_loss_list != None:
                plt.figure(figsize=(14, 5))
                plt.plot(Q_loss_list, label="Q_loss")
                plt.xlabel("Date")
                plt.ylabel("Thermal losses in W")
                plt.title(f"PipeID {edge_data.get('pipeID', None)} Themal loss")
                plt.legend()
                plt.tight_layout()
                plt.grid(True)
                plt.savefig(output_dir/ f"R_pipe_Q_loss_{edge_data.get('pipeID', None)}.png", dpi=300)
                plt.close()

    def retransform_pipe_geojson_data(self, geojson_path: Path):
        """Transforms the data of the pipe onto the geojson that are given back"""
        logger = set_up_file_logger("retransform_pipe_geojson_data", level=20)

        logger.info("=" * 80)
        logger.info("RETRANSFORM PIPE DATA TO GEOJSON")
        logger.info("=" * 80)

        logger.info(f"Analyzing: {self.root_path}")
        logger.info(f"Supply Side UESGraph: {self.graph_supply_json}")
        logger.info(f"Return Side UESGraph: {self.graph_return_json}")

        # Load UESGraph
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: LOAD SUPPLY and RETURN NETWORK")
        logger.info("=" * 80)

        logger.info(f"Loading from JSON: {self.graph_supply_json}")
        graph = ug.UESGraph()
        graph.from_json(path=str(self.graph_supply_json), network_type="heating")
        logger.info(f"Loaded {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        
        logger.info(f"Loading from JSON: {self.graph_return_json}")
        graph_return = ug.UESGraph()
        graph_return.from_json(path=str(self.graph_return_json), network_type="heating")
        logger.info(f"Loaded {len(graph_return.nodes)} nodes, {len(graph_return.edges)} edges")

        with open(geojson_path, 'r') as f:
            geo_data = json.load(f)

        # Add Q_loss from simulation data (should already be in edges if assigned correctly)
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: RETRANSFORM DATA TO GEOJSON")
        logger.info("=" * 80)

        output_dir = self.root_path / "analysis_outputs" / "geojsons"
        output_dir.mkdir(parents=True, exist_ok=True)

        edge_dict = {}
        for edge in graph.edges():
            edge_data = graph.edges[edge]
            edge_data_R = graph_return.edges[edge]

            edge_id = edge_data["attr_dict"].get("id") 

            if edge_id is None:
                continue

            edge_dict[edge_id] = {
                "supply": {
                    "m_flow": edge_data.get("m_flow"),
                    "T_in": edge_data.get("T_in"),
                    "T_out": edge_data.get("T_out"),
                    "Q_loss": edge_data.get("Q_loss"),
                },
                "return": {
                    "m_flow": edge_data_R.get("m_flow"),
                    "T_in": edge_data_R.get("T_in"),
                    "T_out": edge_data.get("T_out"),
                    "Q_loss": edge_data.get("Q_loss"),
                }
            }

        geo_data_supply = copy.deepcopy(geo_data)
        geo_data_return = copy.deepcopy(geo_data)

        for feature_s, feature_r in zip(geo_data_supply["features"], geo_data_return["features"]):
            geo_id = feature_s["properties"].get("id")

            if geo_id in edge_dict:
                # Supply
                feature_s["properties"].update(edge_dict[geo_id]["supply"])

                # Return
                feature_r["properties"].update(edge_dict[geo_id]["return"])

        with open(output_dir / "network_S_data.geojson", 'w') as f:
            json.dump(geo_data_supply, f, indent=4)

        with open(output_dir / "network_R_data.geojson", 'w') as f:
            json.dump(geo_data_return, f, indent=4)

    def visualize_network(self, time_index: int):
        """ Visualizes for a specified time index the network with mass flow, pressure difference, 
            pressure and temperature as attributes for supply and return side
        
        Parameters:
            time_index : int, the index of the timestep to visualize (0-based)    
        """
        logger = set_up_file_logger("visualize_network", level=20)

        logger.info("=" * 80)
        logger.info("Visualize Network at Timestep")
        logger.info("=" * 80)

        logger.info(f"Analyzing: {self.root_path}")
        logger.info(f"Supply Side UESGraph: {self.graph_supply_json}")
        logger.info(f"Return Side UESGraph: {self.graph_return_json}")

        # Load UESGraph
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: LOAD SUPPLY and RETURN NETWORK")
        logger.info("=" * 80)

        logger.info(f"Loading from JSON: {self.graph_supply_json}")
        graph = ug.UESGraph()
        graph.from_json(path=str(self.graph_supply_json), network_type="heating")
        logger.info(f"Loaded {len(graph.nodes)} nodes, {len(graph.edges)} edges")
        
        logger.info(f"Loading from JSON: {self.graph_return_json}")
        graph_return = ug.UESGraph()
        graph_return.from_json(path=str(self.graph_return_json), network_type="heating")
        logger.info(f"Loaded {len(graph_return.nodes)} nodes, {len(graph_return.edges)} edges")
        
        output_dir = self.root_path / "analysis_outputs" / "network_visualization"
        output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: VISUALIZE NETWORK AT TIMESTEP")
        logger.info("=" * 80)

        vis = ug.Visuals(graph)
        for edge in graph.edges:
            graph.edges[edge]["m_flow"] = abs(graph.edges[edge]["m_flow"][time_index])
            graph.edges[edge]["dp"] = abs(graph.edges[edge]["dp"][time_index])
        vis.show_network(show_plot=False,
                            scaling_factor=1,
                            scaling_factor_diameter=50,
                            label_size=15,
                            ylabel="Mass flow in kg/s",
                            generic_extensive_size="m_flow",
                            save_as=os.path.join(output_dir,"m_flow.png"),
                            timestamp="Mass flow"
                            )
        vis.show_network(show_plot=False,
                            scaling_factor=1,
                            scaling_factor_diameter=50,
                            label_size=15,
                            ylabel="Pressure difference in Pa",
                            generic_extensive_size="dp",
                            save_as=os.path.join(output_dir,"dp.png"),
                            timestamp="Pressure difference"
                            )
        
        for node in graph.nodes:
            graph.nodes[node]["p"] = graph.nodes[node]["pressure"][time_index]
            graph.nodes[node]["T"] = graph.nodes[node]["temperature"][time_index]
        vis.show_network(show_plot=False,
                            scaling_factor=1,
                            scaling_factor_diameter=50,
                            ylabel="Pressure in Pa",
                            label_size=15,
                            generic_intensive_size="p",
                            save_as=os.path.join(output_dir,"pressure.png"),
                            timestamp="Pressure"
                            )
        vis.show_network(show_plot=False,
                            scaling_factor=1,
                            scaling_factor_diameter=50,
                            ylabel="Temperature in K",
                            label_size=15,
                            generic_intensive_size="T",
                            save_as=os.path.join(output_dir,"temperature.png"),
                            timestamp="Temperature"
                            )

        vis_return = ug.Visuals(graph_return)
        for edge in graph.edges:
            graph_return.edges[edge]["m_flow"] = abs(graph_return.edges[edge]["m_flow"][time_index])
            graph_return.edges[edge]["dp"] = abs(graph_return.edges[edge]["dp"][time_index])
        vis_return.show_network(show_plot=False,
                            scaling_factor=1,
                            scaling_factor_diameter=50,
                            label_size=15,
                            ylabel="Mass flow in kg/s",
                            generic_extensive_size="m_flow",
                            save_as=os.path.join(output_dir,"m_flow_R.png"),
                            timestamp="Mass flow"
                            )
        vis_return.show_network(show_plot=False,
                            scaling_factor=1,
                            scaling_factor_diameter=50,
                            label_size=15,
                            ylabel="Pressure difference in Pa",
                            generic_extensive_size="dp",
                            save_as=os.path.join(output_dir,"dp_R.png"),
                            timestamp="Pressure difference"
                            )
        
        for node in graph.nodes:
            graph_return.nodes[node]["p"] = graph_return.nodes[node]["pressure"][time_index]
            graph_return.nodes[node]["T"] = graph_return.nodes[node]["temperature"][time_index]
        vis_return.show_network(show_plot=False,
                            scaling_factor=1,
                            scaling_factor_diameter=50,
                            ylabel="Pressure in Pa",
                            label_size=15,
                            generic_intensive_size="p",
                            save_as=os.path.join(output_dir,"pressure_R.png"),
                            timestamp="Pressure"
                            )
        vis_return.show_network(show_plot=False,
                            scaling_factor=1,
                            scaling_factor_diameter=50,
                            ylabel="Temperature in K",
                            label_size=15,
                            generic_intensive_size="T",
                            save_as=os.path.join(output_dir,"temperature_R.png"),
                            timestamp="Temperature"
                            )   

            

        