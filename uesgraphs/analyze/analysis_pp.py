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

        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: PLOT PIPE TEMPERATURES")
        logger.info("=" * 80)

        output_dir = self.root_path / "analysis_outputs" / "pipe_temperatures"
        output_dir.mkdir(parents=True, exist_ok=True)

        for edge in graph.edges:
            edge_data = graph.edges[edge]
            temp_from_list = np.array(edge_data.get("t_from", None))
            temp_to_list = np.array(edge_data.get("t_outlet", None)) 
            '''
            plt.figure(figsize=(14, 5))
            plt.plot(temp_from_list, label="T_from")
            plt.plot(temp_to_list, label="T_to")
            plt.xlabel("Date")
            plt.ylabel("Temperature in °C")
            plt.title(f"PipeID {edge_data.get('pipeID', None)} Temperatures")
            plt.legend()
            plt.tight_layout()
            plt.grid(True)
            plt.savefig(output_dir/ f"pipe_temp_{edge_data.get('pipeID', None)}.png", dpi=300)
            plt.close()
            '''
            if temp_from_list.all() != None and temp_to_list.all() != None:
                plt.figure(figsize=(14, 5))
                plt.plot(temp_from_list - temp_to_list, label="dT")
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
            plt.figure(figsize=(14, 5))
            plt.plot(Q_loss_list, label="m_flow")
            plt.xlabel("Date")
            plt.ylabel("Thermal losses in W")
            plt.title(f"PipeID {edge_data.get('pipeID', None)} Themal loss")
            plt.legend()
            plt.tight_layout()
            plt.grid(True)
            plt.savefig(output_dir/ f"pipe_Q_loss_{edge_data.get('pipeID', None)}.png", dpi=300)
            plt.close()
        
        logger.info(f"Loading from JSON: {self.graph_return_json}")
        graph_return = ug.UESGraph()
        graph_return.from_json(path=str(self.graph_return_json), network_type="heating")
        logger.info(f"Loaded {len(graph_return.nodes)} nodes, {len(graph_return.edges)} edges")

        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: PLOT PIPE TEMPERATURES")
        logger.info("=" * 80)

        output_dir = self.root_path / "analysis_outputs" / "pipe_temperatures"
        output_dir.mkdir(parents=True, exist_ok=True)

        for edge in graph_return.edges:
            edge_data = graph_return.edges[edge]
            temp_from_list = np.array(edge_data.get("t_from", None))
            temp_to_list = np.array(edge_data.get("t_outlet", None)) 
            '''
            plt.figure(figsize=(14, 5))
            plt.plot(temp_from_list, label="T_from")
            plt.plot(temp_to_list, label="T_to")
            plt.xlabel("Date")
            plt.ylabel("Temperature in °C")
            plt.title(f"PipeID {edge_data.get('pipeID', None)} Temperatures")
            plt.legend()
            plt.tight_layout()
            plt.grid(True)
            plt.savefig(output_dir/ f"pipe_temp_{edge_data.get('pipeID', None)}.png", dpi=300)
            plt.close()
            '''
            if temp_from_list.all() != None and temp_to_list.all() != None:
                plt.figure(figsize=(14, 5))
                plt.plot(temp_from_list - temp_to_list, label="dT")
                plt.xlabel("Index")
                plt.ylabel("Temperature in °C")
                plt.title(f"PipeID {edge_data.get('pipeID', None)} Temperatures")
                plt.legend()
                plt.tight_layout()
                plt.grid(True)
                plt.savefig(output_dir/ f"R_pipe_temp_df_{edge_data.get('pipeID', None)}.png", dpi=300)
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
                plt.savefig(output_dir/ f"R_pipe_m_flow_{edge_data.get('pipeID', None)}.png", dpi=300)
                plt.close()

            Q_loss_list = edge_data.get("Q_loss", None)
            plt.figure(figsize=(14, 5))
            plt.plot(Q_loss_list, label="m_flow")
            plt.xlabel("Date")
            plt.ylabel("Thermal losses in W")
            plt.title(f"PipeID {edge_data.get('pipeID', None)} Themal loss")
            plt.legend()
            plt.tight_layout()
            plt.grid(True)
            plt.savefig(output_dir/ f"R_pipe_Q_loss_{edge_data.get('pipeID', None)}.png", dpi=300)
            plt.close()

        