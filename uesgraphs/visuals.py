# -*- coding:utf8 -*-
"""
This module contains visualization tools for uesgraphs
"""

import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
from matplotlib.collections import LineCollection
from matplotlib import gridspec
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
import random
import shapely.geometry as sg
import sys
import warnings
from matplotlib.lines import Line2D
import matplotlib.lines as mlines
from matplotlib.colors import Normalize

#For logging
import logging
import tempfile
from datetime import datetime
import os

def set_up_logger(name,log_dir = None,level=int(logging.ERROR)):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if log_dir == None:
            log_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
        print(f"Logfile findable here: {log_file}")
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger


class Visuals(object):
    """
    Visualizes a uesgraph by networkX graph drawing

    Parameters
    ----------

    uesgraph : uesgraphs.uesgraph.UESGraph object
        The visualization output will be following the graph layout
        specified in the input uesgraph
    """

    def __init__(self, uesgraph,log_level = logging.DEBUG):
        """
        Constructor for `Visuals`
        """
        self.uesgraph = uesgraph
        self.logger = set_up_logger("Visuals",level=log_level)
        self.logger.info("Visuals object created")

    def create_plot_simple(self, ax, scaling_factor=0.5):
        """Creates a very simple plot setup for fast performance

        Parameters
        ----------
        ax : maplotlib ax object
        scaling_factor : float
            Factor that scales the sized of node dots in the plot relative to
            the edge widths

        Returns
        -------
        ax : maplotlib ax object
        """
        counter = 0

        for street in self.uesgraph.nodelist_street:
            ax.scatter(
                self.uesgraph.node[street]["position"].x,
                self.uesgraph.node[street]["position"].y,
                s=scaling_factor,
                color="grey",
                alpha=0.7,
            )

        for nodelist_heating in list(self.uesgraph.nodelists_heating.values()):
            for heating_node in nodelist_heating:
                y_offset = random.choice([0.0001, 0.0002, 0.00015])
                x_offset = random.choice([0.0005, 0.00055, 0.0006, 0.00065, 0.0007])
                ax.scatter(
                    self.uesgraph.node[heating_node]["position"].x,
                    self.uesgraph.node[heating_node]["position"].y,
                    s=scaling_factor * 15,
                    color="#8B0000",
                    alpha=0.7,
                )

        for edge in self.uesgraph.edges():
            for node in edge:
                color = "black"
                style = "solid"
                alpha = 1
                linewidth = 0.2
                if "street" in self.uesgraph.node[node]["node_type"]:
                    color = "grey"
                    style = "solid"
                    alpha = 0.7
                    linewidth = 1.5
                    break
                elif "heat" in self.uesgraph.node[node]["node_type"]:
                    color = "#8B0000"
                    style = "solid"
                    linewidth = 1
                    alpha = 1
                    break
                elif "cool" in self.uesgraph.node[node]["node_type"]:
                    color = "#1874CD"
                    style = "solid"
                    linewidth = 1
                    alpha = 1
                    break
            ax.plot(
                [
                    self.uesgraph.node[edge[0]]["position"].x,
                    self.uesgraph.node[edge[1]]["position"].x,
                ],
                [
                    self.uesgraph.node[edge[0]]["position"].y,
                    self.uesgraph.node[edge[1]]["position"].y,
                ],
                color=color,
                linewidth=linewidth,
                alpha=alpha,
            )

        for building in self.uesgraph.nodelist_building:
            if self.uesgraph.node[building]["position"] is not None:
                if self.uesgraph.node[building]["is_supply_heating"] is False:
                    ax.scatter(
                        self.uesgraph.node[building]["position"].x,
                        self.uesgraph.node[building]["position"].y,
                        s=scaling_factor * 3,
                        color="#CD3700",
                        alpha=0.7,
                    )
                else:
                    ax.scatter(
                        self.uesgraph.node[building]["position"].x,
                        self.uesgraph.node[building]["position"].y,
                        s=scaling_factor * 25,
                        color="#8B0000",
                        alpha=0.7,
                    )
                counter += 1

        if "proximity" in self.uesgraph.graph:
            try:
                poly = self.uesgraph.graph["proximity"]
                x, y = poly.exterior.xy
                ax.plot(
                    x,
                    y,
                    color="#8B0000",
                    alpha=0.7,
                    linewidth=1,
                    solid_capstyle="round",
                    zorder=2,
                )
            except:
                None

        plt.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            labelbottom=False,
            right=False,
            left=False,
            labelleft=False,
        )

        plt.axis("equal")
        ax.get_xaxis().get_major_formatter().set_useOffset(False)
        ax.axis("off")

        return ax

    def _place_text(self, element):
        """
        Returns a point object where to place text in a plot

        Parameters
        ----------
        element : int or list
            Node or edge identifier for the node which should be labeled with
            text

        Returns
        -------
        text_pos : shapely.geometry.Point object
            Position of the text
        """
        if sys.version_info < (3, 6):
            warnings.warn(
                "The placement of elements in versions older than"
                "Python 3.6 may differ from the 3.6 placement"
            )

        diagonal = self.uesgraph.max_position.distance(self.uesgraph.min_position)
        curr_scaling = diagonal * 0.04

        if isinstance(element, tuple):
            edge = element
            pos_0 = self.uesgraph.node[edge[0]]["position"]
            pos_1 = self.uesgraph.node[edge[1]]["position"]

            parallel_line = sg.LineString([pos_0, pos_1]).parallel_offset(
                curr_scaling / 2
            )
            text_pos = sg.Point(
                parallel_line.centroid.x, parallel_line.centroid.y - curr_scaling / 4.0
            )

        else:
            node = element

            node_pos = self.uesgraph.node[node]["position"]
            neighbors = list(self.uesgraph.neighbors(node))
            if len(neighbors) > 1:
                # Find 2 nearest neighbors `neighbor_0` and `neighbor_1`
                distances = {}
                for neighbor in neighbors:
                    neighbor_pos = self.uesgraph.node[neighbor]["position"]
                    distances[neighbor] = neighbor_pos.distance(node_pos)
                neighbor_0 = min(distances, key=distances.get)
                del distances[neighbor_0]
                neighbor_1 = min(distances, key=distances.get)

                neighbor_0_pos = self.uesgraph.node[neighbor_0]["position"]
                neighbor_1_pos = self.uesgraph.node[neighbor_1]["position"]

                # Find `ref_point` between both nearest neighbors
                ref_point = sg.LineString([neighbor_0_pos, neighbor_1_pos]).centroid
                text_pos = ref_point
                plt.plot(
                    [text_pos.x, node_pos.x],
                    [text_pos.y, node_pos.y],
                    "--",
                    color="black",
                    alpha=0.7,
                )
            elif len(neighbors) == 0:
                text_pos = self.uesgraph.node[node]["position"]
            else:
                neighbor_pos = self.uesgraph.node[neighbors[0]]["position"]

                dx = node_pos.x - neighbor_pos.x
                dy = node_pos.y - neighbor_pos.y
                opposite = sg.Point(node_pos.x + dx, node_pos.y + dy)

                dis = opposite.distance(node_pos)

                ring_distance = curr_scaling

                if ring_distance > dis:
                    ring_distance = dis / 1.6

                text_pos = node_pos.buffer(ring_distance).exterior.intersection(
                    sg.LineString([node_pos, opposite])
                )

        return text_pos

    def create_plot(
        self,
        ax,
        labels=None,
        show_diameters=False,
        show_mass_flows=False,
        show_press_flows=False,
        show_press_drop_flows=False,
        show_velocity=False,
        show_temperature_drop=False,
        label_size=7,
        edge_markers=[],
        node_markers=[],
        add_diameter=False,
        add_edge_temperatures=False,
        add_edge_flows=False,
        add_edge_pressures=False,
        add_edge_pressure_drop=False,
        add_edge_velocity=False,
        add_temperature_drop=False,
        add_temperature_diff=False,
        directions=False,
        scaling_factor=1.5,
        scaling_factor_diameter=5,
        minmaxtemp = False,
        minmaxmflow = False,
        minmaxmpress = False,
        minmaxmpressdrop = False,
        minmaxmvelocity = False,
        minmaxmtempdrop = False,
        generic_intensive_size=None,
        generic_extensive_size=None,
        minmax = False,
        zero_alpha = 1,
        cmap = "viridis",
    ):
        """Creates the plot setup, that can be shown or saved to file

        Parameters
        ----------
        ax : maplotlib ax object
        labels : str
            If set to `'street'`, node numbers of street nodes are shown in
            plot
        show_diameters : boolean
            True if edges of heating networks should show the relative diameter
            of the pipe, False if not
        show_mass_flows : boolean
            True if edges of heating networks should show the mass flow rate
            through the pipe, False if not
        show_press_flows : boolean
            True if edges of heating networks should show the pressure
            through the pipe, False if not
        show_press_drop_flows : boolean
            True if edges of heating networks should show the pressure drop 
            through the pipe, False if not
        label_size : int
            Fontsize for optional labels
        edge_markers : list
            A list of edges that should be marked in the plot
        node_markers : list
            A list of nodes that should be marked in the plot
        add_edge_temperatures : boolean
            Plots edge temperatures on top of plot if True
        add_edge_flows : boolean
            Plots edge width according to flow rates in the networks if True
        add_edge_pressures : boolean
            Plots edge pressure on top of plot if True
        add_edge_pressure_drop : boolean
            Plots edge pressure drop on top of plot if True
        add_edge_electricity : boolean
            Plots edge electricity on top of plot if True
        directions : boolean
            Plots arrows for flow directions if True; If add_edge_flows is
            False, these arrows will show the initial assumed flow direction.
            If add_edge_flows is True, the arrows show the calculated flow
            direction.
        scaling_factor : float
            Factor that scales the sized of node dots in the plot relative to
            the edge widths
        scaling_factor_diameter : float
            Factor that scales the width of lines for show_diameters = True
        generic_intensive_size : str
            If set to a string, the edges will be colored according to the
            values of the attribute with the given string
        generic_extensive_size : str
            If set to a string, the edges will be colored according to the
            values of the attribute with the given string
        minmax : array
            Contains the minimum and maximum values for the generic size
            in format [min, max]
        zero_alpha: float
            Alpha value to paint certain edges transparent. Look at docstring
            of paint_edges_extensive_sizes for more information
        cmap : str, optional
            Name of the colormap to use for visualization (default='viridis').
            Common options include 'viridis', 'coolwarm', 'RdYlGn', 'plasma', 
            'Blues'. For temperature data, 'coolwarm' or 'RdYlGn' provide 
            intuitive red=hot, blue=cold color semantics.
        Returns
        -------
        ax : maplotlib ax object
        """
        if show_press_flows is True:
            press_flow_max = 0
            volume_flows = [0]
            for edge in self.uesgraph.edges():
                if "press_flow" in self.uesgraph.edges[edge[0], edge[1]]:
                    curr_m = abs(self.uesgraph.edges[edge[0], edge[1]]["press_flow"])
                    if curr_m > press_flow_max:
                        press_flow_max = curr_m
                        
        if show_press_drop_flows is True:
            press_drop_flow_max = 0
            volume_flows = [0]
            for edge in self.uesgraph.edges():
                if "press_drop_flow" in self.uesgraph.edges[edge[0], edge[1]]:
                    curr_m = abs(self.uesgraph.edges[edge[0], edge[1]]["press_drop_flow"])
                    if curr_m > press_drop_flow_max:
                        press_drop_flow_max = curr_m
                        
        if show_temperature_drop is True:
            temperature_drop_max = 0
            for edge in self.uesgraph.edges():
                if "temperature_drop" in self.uesgraph.edges[edge[0], edge[1]]:
                    curr_m = abs(self.uesgraph.edges[edge[0], edge[1]]["temperature_drop"])
                    if curr_m > temperature_drop_max:
                        temperature_drop_max = curr_m  
                                      
        if show_velocity is True:
            velocity_max = 0
            volume_flows = [0]
            for edge in self.uesgraph.edges():
                if "velocity" in self.uesgraph.edges[edge[0], edge[1]]:
                    curr_m = abs(self.uesgraph.edges[edge[0], edge[1]]["velocity"])
                    if curr_m > velocity_max:
                        velocity_max = curr_m
            
        for street in self.uesgraph.nodelist_street:
            draw = nx.draw_networkx_nodes(
                self.uesgraph,
                pos=self.uesgraph.positions,
                nodelist=[street],
                node_size=2 * scaling_factor,
                node_color="black",
                linewidths=None,
                alpha=0.2,
            )
            if labels == "street":
                plt.text(
                    self.uesgraph.node[street]["position"].x,
                    self.uesgraph.node[street]["position"].y,
                    s=str(street),
                    horizontalalignment="center",
                    fontsize=label_size,
                )
            if draw is not None:
                draw.set_edgecolor("black")

        for heat_network in self.uesgraph.nodelists_heating.keys():
            for node in self.uesgraph.nodelists_heating[heat_network]:
                # color #8B0000 slightly #8B0000
                draw = nx.draw_networkx_nodes(
                    self.uesgraph,
                    pos=self.uesgraph.positions,
                    nodelist=[node],
                    node_color="#8B0000",
                    node_size=3 * scaling_factor,
                    linewidths=None,
                    alpha=0.7,
                )
                if labels == "heat":
                    plt.text(
                        self.uesgraph.node[node]["position"].x,
                        self.uesgraph.node[node]["position"].y,
                        s=str(node),
                        horizontalalignment="center",
                        fontsize=label_size,
                    )
                if labels == "name":
                    if "name" in self.uesgraph.node[node]:
                        text_pos = self._place_text(node)
                        plt.text(
                            text_pos.x,
                            text_pos.y,
                            s=str(self.uesgraph.node[node]["name"]),
                            horizontalalignment="center",
                            fontsize=label_size,
                        )
                if draw is not None:
                    draw.set_edgecolor("#8B0000")
        for cool_network in self.uesgraph.nodelists_cooling.keys():
            for node in self.uesgraph.nodelists_cooling[cool_network]:
                draw = nx.draw_networkx_nodes(
                    self.uesgraph,
                    pos=self.uesgraph.positions,
                    nodelist=[node],
                    node_color="#1874CD",
                    node_size=1,
                    linewidths=None,
                    alpha=0.7,
                )
                if draw is not None:
                    draw.set_edgecolor("#1874CD")
        for elec_network in self.uesgraph.nodelists_electricity.keys():
            for node in self.uesgraph.nodelists_electricity[elec_network]:
                draw = nx.draw_networkx_nodes(
                    self.uesgraph,
                    pos=self.uesgraph.positions,
                    nodelist=[node],
                    node_color="orange",
                    node_size=3 * scaling_factor,
                    linewidths=None,
                )
                if draw is not None:
                    draw.set_edgecolor("orange")
        for gas_network in self.uesgraph.nodelists_gas.keys():
            for node in self.uesgraph.nodelists_gas[gas_network]:
                draw = nx.draw_networkx_nodes(
                    self.uesgraph,
                    pos=self.uesgraph.positions,
                    nodelist=[node],
                    node_color="gray",
                    node_size=3 * scaling_factor,
                    linewidths=None,
                )
                if draw is not None:
                    draw.set_edgecolor("gray")
        for other_network in self.uesgraph.nodelists_others.keys():
            for node in self.uesgraph.nodelists_others[other_network]:
                draw = nx.draw_networkx_nodes(
                    self.uesgraph,
                    pos=self.uesgraph.positions,
                    nodelist=[node],
                    node_color="purple",
                    node_size=3 * scaling_factor,
                    linewidths=None,
                )
                if draw is not None:
                    draw.set_edgecolor("purple")

        for building in self.uesgraph.nodelist_building:
            if self.uesgraph.node[building]["position"] is not None:
                if self.uesgraph.node[building]["is_supply_heating"] is True:
                    draw = nx.draw_networkx_nodes(
                        self.uesgraph,
                        pos=self.uesgraph.positions,
                        nodelist=[building],
                        node_color="#8B0000",
                        node_size=90 * scaling_factor,
                        linewidths=None,
                    )
                    if draw is not None:
                        draw.set_edgecolor("grey")
                        
                    # # Get the name of the building
                    # building_name = self.uesgraph.node[building]["name"]

                    # # Get the position of the building
                    # building_pos = self.uesgraph.positions[building]

                    # # Adjust the position of the text
                    # text_pos = (building_pos[0], building_pos[1] + 15)  # Adjust the 0.02 as needed

                    # # Set the font size
                    # font_size = 15  # Adjust as needed

                    # # Format the text
                    # text = f'{building_name}'

                    # # Plot the name of the building at its position
                    # plt.text(text_pos[0], text_pos[1], text, 
                    # horizontalalignment='center', verticalalignment='center', fontsize=font_size)
                    
                if self.uesgraph.node[building]["is_supply_cooling"] is True:
                    draw = nx.draw_networkx_nodes(
                        self.uesgraph,
                        pos=self.uesgraph.positions,
                        nodelist=[building],
                        node_color="#1874CD",
                        node_size=60 * scaling_factor,
                        linewidths=None,
                    )
                    if draw is not None:
                        draw.set_edgecolor("#1874CD")
                        
                    # # Get the name of the building
                    # building_name = self.uesgraph.node[building]["name"]

                    # # Get the position of the building
                    # building_pos = self.uesgraph.positions[building]

                    # # Adjust the position of the text
                    # text_pos = (building_pos[0], building_pos[1] + 15)  # Adjust the 0.02 as needed

                    # # Set the font size
                    # font_size = 15  # Adjust as needed

                    # # Format the text
                    # text = f'{building_name}'

                    # # Plot the name of the building at its position
                    # plt.text(text_pos[0], text_pos[1], text, 
                    # horizontalalignment='center', verticalalignment='center', fontsize=font_size)
                    
                if self.uesgraph.node[building]["is_supply_gas"] is True:
                    draw = nx.draw_networkx_nodes(
                        self.uesgraph,
                        pos=self.uesgraph.positions,
                        nodelist=[building],
                        node_color="gray",
                        node_size=40 * scaling_factor,
                        linewidths=None,
                    )
                    if draw is not None:
                        draw.set_edgecolor("gray")
                        
                    
                # color light black
                draw = nx.draw_networkx_nodes(
                    self.uesgraph,
                    pos=self.uesgraph.positions,
                    nodelist=[building],
                    node_size=25 * scaling_factor,
                    node_color="#2B2B2B",
                    linewidths=None,
                    alpha=0.7,
                )
                # Get the name of the building
                building_name = self.uesgraph.node[building]["name"]
                
                # Get the position of the building
                building_pos = self.uesgraph.positions[building]

                # # Adjust the position of the text
                # text_pos = (building_pos[0], building_pos[1] + 15)  # Adjust the 0.02 as needed

                # # Set the font size
                # font_size = 15  # Adjust as needed

                # # Format the text
                # text = f'{building_name}'
                
                # # Plot the name of the building at its position
                # plt.text(text_pos[0], text_pos[1], text, 
                # horizontalalignment='center', verticalalignment='center', fontsize=font_size)
                
                if labels == "building":
                    plt.text(
                        self.uesgraph.node[building]["position"].x,
                        self.uesgraph.node[building]["position"].y,
                        s=str(building),
                        horizontalalignment="center",
                        fontsize=label_size,
                    )
                elif labels == "name":
                    if "name" in self.uesgraph.node[building]:
                        text_pos = self._place_text(building)
                        plt.text(
                            text_pos.x,
                            text_pos.y,
                            s=self.uesgraph.node[building]["name"],
                            horizontalalignment="center",
                            fontsize=label_size,
                        )
                if draw is not None:
                    draw.set_edgecolor("grey")

                if self.uesgraph.node[building]["is_supply_electricity"] is True:
                    draw = nx.draw_networkx_nodes(
                        self.uesgraph,
                        pos=self.uesgraph.positions,
                        nodelist=[building],
                        node_color="orange",
                        node_size=12 * scaling_factor,
                        linewidths=None,
                        alpha=0.8,
                    )
                    if draw is not None:
                        draw.set_edgecolor("orange")
                if self.uesgraph.node[building]["is_supply_other"] is True:
                    draw = nx.draw_networkx_nodes(
                        self.uesgraph,
                        pos=self.uesgraph.positions,
                        nodelist=[building],
                        node_color="purple",
                        node_size=5 * scaling_factor,
                        linewidths=None,
                        alpha=0.5,
                    )
                    if draw is not None:
                        draw.set_edgecolor("purple")

        #Lets draw some edges!
        for edge in self.uesgraph.edges():
            for node in edge:
                color = "black"
                style = "solid"
                alpha = 1
                if "street" in self.uesgraph.node[node]["node_type"]:
                    color = "black"
                    style = "solid"
                    alpha = 0.2
                    break
                elif "heat" in self.uesgraph.node[node]["node_type"]:
                    color = "#8B0000"
                    style = "solid"
                    alpha = 0.8
                    break
                elif "cool" in self.uesgraph.node[node]["node_type"]:
                    color = "#1874CD"
                    style = "solid"
                    alpha = 0.8
                    break
                elif "elec" in self.uesgraph.node[node]["node_type"]:
                    color = "orange"
                    style = "dotted"
                    alpha = 0.8
                    break
                elif "gas" in self.uesgraph.node[node]["node_type"]:
                    color = "gray"
                    style = "dashdot"
                    alpha = 0.8
                    break
                elif "others" in self.uesgraph.node[node]["node_type"]:
                    color = "purple"
                    style = "dashdot"
                    alpha = 0.8
                    break
            #Lets draw!
            nx.draw_networkx_edges(
                   self.uesgraph,
                   pos=self.uesgraph.positions,
                   edgelist=[edge],
                   style=style,
                   edge_color=[color],
                   alpha=alpha,
                )
            
            
            
            if labels == "name":
                if "name" in self.uesgraph.edges[edge[0], edge[1]]:
                    text_pos = self._place_text(edge)
                    plt.text(
                        text_pos.x,
                        text_pos.y,
                        s=self.uesgraph.edges[edge[0], edge[1]]["name"],
                        horizontalalignment="center",
                        fontsize=label_size,
                    )

        if labels == "all_nodes":
            for node in self.uesgraph.nodes():
                plt.text(
                    self.uesgraph.node[node]["position"].x,
                    self.uesgraph.node[node]["position"].y,
                    s=str(node),
                    horizontalalignment="center",
                    fontsize=label_size,
                )
        
        #Plotting of extensive sizes
        if show_mass_flows is True:
            self._paint_edges_extensive_sizes(
                ax,
                key="mass_flow",
                minmax=minmaxmflow,
                scaling_factor_diameter=scaling_factor_diameter,
                zero_alpha=zero_alpha,
                cmap = cmap
            )
        
        if show_press_drop_flows is True:
            self._paint_edges_extensive_sizes(
                ax,
                key="press_drop_flow",
                minmax=minmaxmpressdrop,
                scaling_factor_diameter=scaling_factor_diameter,
                zero_alpha=zero_alpha,
                cmap = cmap
            )
        
        if show_temperature_drop is True:   
            self._paint_edges_extensive_sizes(
                ax,
                key="temperature_drop",
                minmax=minmaxmtempdrop,
                scaling_factor_diameter=scaling_factor_diameter,
                zero_alpha=zero_alpha,
                cmap = cmap
            )

        if show_velocity is True:
            self._paint_edges_extensive_sizes(
                ax,
                key="velocity",
                minmax=minmaxmvelocity,
                scaling_factor_diameter=scaling_factor_diameter,
                zero_alpha=zero_alpha,
                cmap = cmap
            )

        #Plotting of intensive sizes
        if add_edge_temperatures is True:
            self._paint_edges_intensive_sizes(
                ax,
                "temperature_supply",
                scaling_factor_diameter=scaling_factor_diameter,
                minmax=minmaxtemp,
                cmap = cmap
            )
        if show_press_flows is True:
            self._paint_edges_intensive_sizes(
                ax,
                key="press_flow",
                scaling_factor_diameter=scaling_factor_diameter,
                minmax=minmaxmpress,
                cmap = cmap
            )

        if show_diameters is True:
            self._paint_edges_diameter(
                ax,
                scaling_factor_diameter=scaling_factor_diameter
                )
        if generic_intensive_size is not None:
            self._paint_edges_intensive_sizes(
                ax,
                key = generic_intensive_size,
                scaling_factor_diameter=scaling_factor_diameter,
                minmax=minmax,
                cmap = cmap
            )
        if generic_extensive_size is not None:
            self._paint_edges_extensive_sizes(
                ax,
                key = generic_extensive_size,
                minmax=minmax,
                scaling_factor_diameter=scaling_factor_diameter,
                zero_alpha=zero_alpha,
                cmap = cmap
            )
        
       

        for edge in edge_markers:
            self._add_edge_marker(ax, edge)
        if node_markers != []:
            self._add_node_marker(ax, node_markers, node_size=50 * scaling_factor)

        if directions is True and add_edge_flows is False:
            # Plot arrows for assumed flow direction
            for edge in self.uesgraph.edges():
                pos_0 = self.uesgraph.node[edge[0]]["position"]
                pos_1 = self.uesgraph.node[edge[1]]["position"]
                # center = (pos_0 + pos_1) / 2
                center = sg.LineString([pos_0, pos_1]).centroid
                arrow_head = center.distance(pos_0) / 10
                x = float(center.x)
                y = float(center.y)
                dx = (float(pos_1.x - pos_0.x)) / 4
                dy = (float(pos_1.y - pos_0.y)) / 4

                ax.arrow(
                    x,
                    y,
                    dx,
                    dy,
                    head_width=arrow_head,
                    head_length=arrow_head,
                    linewidth=1,
                    fc="k",
                    ec="k",
                )

        plt.tick_params(
            axis="both",
            which="both",
            bottom=False,
            top=False,
            labelbottom=False,
            right=False,
            left=False,
            labelleft=False,
        )

        plt.axis("equal")
        ax.get_xaxis().get_major_formatter().set_useOffset(False)
        ax.axis("off")

        return ax

    def create_plot_3d(
        self, ax, z_attrib="pressure", show_flow=False, angle=110, label_size=20
    ):
        """Creates the plot setup for a 3d view

        Parameters
        ----------
        ax : maplotlib ax object
        z_attrib : str
            Keyword to control which attribute of nodes will be used for
            the z-coordinate
        show_flow : boolean
            Varies linewidth of the edges if True
        angle : float
            View angle for 3d plot
        label_size : int
            Fontsize for labels

        Returns
        -------
        ax : maplotlib ax object
        """
        if show_flow is True:
            flows = []
            for edge in self.uesgraph.edges():
                flows.append(self.uesgraph.edge[edge[0]][edge[1]]["volume_flow"])
            min_flow = min(flows)
            max_flow = max(flows)
            delta_flow = max_flow - min_flow

            for edge in self.uesgraph.edges():
                flow = self.uesgraph.edge[edge[0]][edge[1]]["volume_flow"]
                weight = ((flow - min_flow) / delta_flow) * 3
                self.uesgraph.edge[edge[0]][edge[1]]["weight"] = weight + 0.1

        for node in self.uesgraph.nodes():
            if z_attrib in self.uesgraph.node[node]:
                x = self.uesgraph.node[node]["position"].x
                y = self.uesgraph.node[node]["position"].y
                z = self.uesgraph.node[node][z_attrib] * 1e-5
                ax.scatter(x, y, zs=z, zdir="z", c="0.5", alpha=0.5)

        for edge in self.uesgraph.edges():
            if (
                z_attrib in self.uesgraph.node[edge[0]]
                and z_attrib in self.uesgraph.node[edge[1]]
            ):
                x = [
                    self.uesgraph.node[edge[0]]["position"].x,
                    self.uesgraph.node[edge[1]]["position"].x,
                ]
                y = [
                    self.uesgraph.node[edge[0]]["position"].y,
                    self.uesgraph.node[edge[1]]["position"].y,
                ]
                z = [
                    self.uesgraph.node[edge[0]][z_attrib] * 1e-5,
                    self.uesgraph.node[edge[1]][z_attrib] * 1e-5,
                ]
                if show_flow is False:
                    ax.plot(x, y, zs=z, zdir="z", ls="-", color="grey", alpha=0.5)
                else:
                    linewidth = self.uesgraph.edge[edge[0]][edge[1]]["weight"]
                    ax.plot(
                        x,
                        y,
                        zs=z,
                        zdir="z",
                        ls="-",
                        color="grey",
                        alpha=0.5,
                        linewidth=linewidth,
                    )
        for node in self.uesgraph.nodes():
            if "is_supply_heating" in self.uesgraph.node[node]:
                if self.uesgraph.node[node]["is_supply_heating"]:
                    x = self.uesgraph.node[node]["position"].x
                    y = self.uesgraph.node[node]["position"].y
                    z = self.uesgraph.node[node][z_attrib] * 1e-5
                    ax.scatter(x, y, zs=z, zdir="z", c="#8B0000")

        ax.view_init(20, angle)
        ax.set_zlabel("Pressure in bar", fontsize=label_size, labelpad=label_size * 2)
        ax.tick_params(labelsize=label_size, pad=label_size)

        ax.set_xticklabels([])
        ax.set_yticklabels([])

        return ax
    
    
    
    def show_network(
        self,
        save_as=None,
        show_plot=True,
        labels=None,
        show_diameters=False,
        show_mass_flows=False,
        show_press_flows=False,
        show_press_drop_flows=False,
        show_velocity=False,
        show_temperature_drop=False,
        label_size=7,
        edge_markers=[],
        node_markers=[],
        add_diameter=False,
        add_edge_temperatures=False,
        add_temperature_drop=False,
        add_temperature_diff=False,
        add_edge_flows=False,
        add_edge_pressures=False,
        add_edge_pressure_drop=False,
        add_edge_velocity=False,
        directions=False,
        scaling_factor=1.5,
        scaling_factor_diameter=5,
        simple=False,
        dpi=150,
        minmaxtemp = False,
        minmaxmflow = False,
        minmaxmpress=False,
        minmaxmpressdrop=False,
        minmaxmvelocity=False,
        minmaxmtempdrop=False,
        timestamp = False,
        generic_intensive_size=None,
        generic_extensive_size=None,
        minmax = None,
        ylabel = None,
        zero_alpha = 1,
        cmap = "viridis"
    ):
        """Shows a plot of the network

        Parameters
        ----------
        save_as : str
            optional parameter, string denoting full path and file name +
            extension for saving the plot
        show_plot : boolean
            True if the plot should be shown in the current Python instance,
            False if not
        labels : str
            If set to `'street'`, node numbers of street nodes are shown in
            plot
        show_diameters : boolean
            True if edges of heating networks should show the relative diameter
            of the pipe, False if not
        show_mass_flows : boolean
            True if edges of heating networks should show the mass flow rate
            through the pipe, False if not
        show_press_flows : boolean
            True if edges of heating networks should show the pressure
            through the pipe, False if not
        show_press_drop_flows : boolean
            True if edges of heating networks should show the pressure drop
            through the pipe, False if not
        label_size : int
            Fontsize for optional labels
        edge_markers : list
            A list of edges that should be marked in the plot
        node_markers : list
            A list of nodes that should be marked in the plot
        add_edge_temperatures : boolean
            Plots edge temperatures on top of plot if True
        add_edge_flows : boolean
            Plots edge width according to flow rates in the networks if True
        add_edge_pressures : boolean
            Plots edge pressure on top of plot if True
        add_edge_pressure_drop : boolean
            Plots edge pressure drop on top of plot if True    
        directions : boolean
            Plots arrows for flow directions if True; If add_edge_flows is
            False, these arrows will show the initial assumed flow direction.
            If add_edge_flows is True, the arrows show the calculated flow
            direction.
        scaling_factor : float
            Factor that scales the sized of node dots in the plot relative to
            the edge widths
        scaling_factor_diameter : float
            Factor that scales the width of lines
        simple : boolean
            For very large uesgraphs, the standard plotting may take too long
            (hours...). In these cases, `simple=True` gives faster results
        dpi : int
            Integer to overwrite the standard resolution of 150 dpi
        minmaxtemp : array
            Array with minimum and maximum temperature value for the scaling 
            of the plot. If not set the values will be calculated automatically
        minmaxmflow : array
            Array with minimum and maximum temperature value for the scaling 
            of the plot. If not set the values will be calculated automatically
        minmaxmpress : array
            Array with minimum and maximum pressure value for the scaling 
            of the plot. If not set the values will be calculated automatically
        minmaxmpressdrop : array
            Array with minimum and maximum pressure drop value for the scaling 
            of the plot. If not set the values will be calculated automatically
        timestamp : datetime
            prints the actual timestamp on the plot
        generic_intensive_size : str
            If set to a string, the edges will be colored according to the
            values of the attribute with the given string
        generic_extensive_size : str
            If set to a string, the edges will be colored according to the
            values of the attribute with the given string
        minmax : array
            Contains the minimum and maximum values for the generic size
            in format [min, max]
        ylabel: str
            Label for the color scale when plotting generic size
        zero_alpha: float
            Alpha value to paint certain edges transparent. Look at docstring
            of paint_edges_extensive_sizes for more information
        cmap : str, optional
            Name of the colormap to use for visualization (default='viridis').
            Common options include 'viridis', 'coolwarm', 'RdYlGn', 'plasma', 
            'Blues'. For temperature data, 'coolwarm' or 'RdYlGn' provide 
            intuitive red=hot, blue=cold color semantics.

        Returns
        -------
        fig : matplotlib.figure.Figure
        """
        self.logger.info("Plotting the network")
        self.logger.debug(f"Plotting the network with the following parameters: minmax: {minmax}) and {ylabel}")
        dx = float(self.uesgraph.max_position.x - self.uesgraph.min_position.x)
        dy = float(self.uesgraph.max_position.y - self.uesgraph.min_position.y)

        if self.uesgraph.max_position.x == self.uesgraph.min_position.x:
            dx = 1
        if self.uesgraph.max_position.y == self.uesgraph.min_position.y:
            dy = 1

        if dx >= dy:
            x_size = 20
            y_size = x_size * dy / dx
        else:
            y_size = 20
            x_size = y_size * dx / dy

        plt.rcParams["figure.figsize"] = x_size, y_size

        #We divide our canvas in two areas. The bigger left one, gs[0], is for the graph
        #  referenced as ax
        # The smaller one, gs[1] on the right is for the color scale
        fig = plt.figure()
        if show_mass_flows is True:
            gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
            ax = plt.subplot(gs[0])
        elif add_edge_temperatures is True:
            gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
            ax = plt.subplot(gs[0])
        elif show_press_flows is True:
            gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
            ax = plt.subplot(gs[0])
        elif show_press_drop_flows is True:
            gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
            ax = plt.subplot(gs[0])
        elif show_velocity is True:
            gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
            ax = plt.subplot(gs[0])
        elif show_diameters is True:
            gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
            ax = plt.subplot(gs[0])
        elif add_temperature_drop is True:
            gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
            ax = plt.subplot(gs[0])
        elif ylabel is not None: #Added for generic sizes in september 2024
            gs = gridspec.GridSpec(1, 2, width_ratios=[20, 1])
            ax = plt.subplot(gs[0])
        else:
            ax = plt.subplot(1, 1, 1)

        if simple is False:
            ax = self.create_plot(
                ax,
                labels=labels,
                show_diameters=show_diameters,
                show_mass_flows=show_mass_flows,
                show_press_flows=show_press_flows,
                show_press_drop_flows=show_press_drop_flows,
                show_velocity=show_velocity,
                show_temperature_drop=show_temperature_drop,
                label_size=label_size,
                edge_markers=edge_markers,
                node_markers=node_markers,
                add_diameter=add_diameter,
                add_edge_temperatures=add_edge_temperatures,
                add_temperature_drop=add_temperature_drop,
                add_temperature_diff=add_temperature_diff,
                add_edge_flows=add_edge_flows,
                add_edge_pressures=add_edge_pressures,
                add_edge_pressure_drop=add_edge_pressure_drop,
                add_edge_velocity=add_edge_velocity,
                directions=directions,
                scaling_factor=scaling_factor,
                scaling_factor_diameter=scaling_factor_diameter,
                minmaxtemp=minmaxtemp,
                minmaxmflow=minmaxmflow,
                minmaxmpress=minmaxmpress,
                minmaxmpressdrop=minmaxmpressdrop,
                minmaxmvelocity=minmaxmvelocity,
                minmaxmtempdrop=minmaxmtempdrop,
                generic_intensive_size=generic_intensive_size,
                generic_extensive_size=generic_extensive_size,
                minmax=minmax,
                zero_alpha=zero_alpha,
                cmap=cmap,
            )
        else:
            ax = self.create_plot_simple(ax, scaling_factor=scaling_factor)

        margin_x = dx / 20
        margin_y = dy / 20
        ax.set_xlim(
            [
                float(self.uesgraph.min_position.x) - margin_x,
                float(self.uesgraph.max_position.x) + margin_x,
            ]
        )
        ax.set_ylim(
            [
                float(self.uesgraph.min_position.y) - margin_y,
                float(self.uesgraph.max_position.y) + margin_y,
            ]
        )
        

        #Here we plot the color scale thats usually on the
        # right side of our final plot gs[1]
        #First we define the minmax-values for the color scale
        # then we assign a ylabel. Magic happens in _add_color_scale()
        self.logger.debug(f"ylabel: {ylabel}")
        cond = True
        if ylabel is not None:
            ylabel = ylabel #ylabel for generic sizes
            self.logger.debug(f"ylabel: {ylabel}")
            if minmax is False or minmax is None:
                if generic_intensive_size is not None:
                    minmax = self.uesgraph.get_min_max(key= generic_intensive_size, mode = "node")
                else:
                    minmax = self.uesgraph.get_min_max(key= generic_extensive_size, mode = "edge")
                self.logger.debug(minmax)
        elif show_mass_flows:
            minmax = minmaxmflow
            if minmax is False or minmax is None:
                minmax = self.uesgraph.get_min_max(key= "mass_flow", mode = "edge")
            ylabel = "Mass Flow in kg/s"
        elif add_edge_temperatures:
            minmax = minmaxtemp
            if minmax is False or minmax is None:
                minmax = self.uesgraph.get_min_max(key= "temperature_supply", mode = "node")
            ylabel = "Temperature in deg C"
        elif add_temperature_drop:
            minmax = minmaxmtempdrop
            if minmax is False or minmax is None:
                minmax = self.uesgraph.get_min_max(key= "temperature_drop", mode = "edge")
            if add_temperature_diff:
                ylabel = "Temperature difference in K"
            else:
                ylabel = "Temperature difference per meter"
        elif show_press_flows:
            minmax = minmaxmpress
            if minmax is False or minmax is None:
                minmax = self.uesgraph.get_min_max(key= "press_flow", mode = "node")
            ylabel = "Pressure in bars"
        elif show_press_drop_flows:
            minmax = minmaxmpressdrop
            if minmax is False or minmax is None:
                minmax = self.uesgraph.get_min_max(key= "press_drop_flow", mode = "edge")
            ylabel = "Pressure drop in bars"
        elif show_velocity:
            minmax = minmaxmvelocity
            ylabel = "velocity in m/s"
        else:
            cond = None
        if cond is not None:
            ax1 = plt.subplot(gs[1])
            self._add_color_scale(ax1,minmax,ylabel, label_size=label_size,cmap=cmap)

        if timestamp:
            ax.text(0.0, 
                -6.0, 
                timestamp,
                fontsize=35,
                # alpha=0.3,
                )

        if save_as is not None:
            plt.savefig(save_as, bbox_inches="tight", dpi=dpi)
            plt.close()
            
        if show_plot is True:
            plt.show()

        return fig

    def show_3d(
        self,
        save_as=None,
        show_plot=True,
        show_flow=False,
        z_attrib="pressure",
        angle=110,
        label_size=20,
    ):
        """Shows an explosion plot of stacked networks in 3d view

        Parameters
        ----------
        save_as : str
            optional parameter, string denoting full path and file name +
            extension for saving the plot
        show_plot : boolean
            True if the plot should be shown in the current Python instance,
            False if not
        show_flow : boolean
            Varies linewidth of the edges if True
        z_attrib : str
            Keyword to control which attribute of nodes will be used for
            the z-coordinate
        angle : float
            View angle for 3d plot
        label_size : int
            Fontsize for optional labels

        Returns
        -------
        fig : matplotlib.figure.Figure
        """
        plt.rcParams["figure.figsize"] = 10, 10

        fig = plt.figure()
        ax = plt.subplot(1, 1, 1, projection="3d")

        ax = self.create_plot_3d(
            ax,
            z_attrib=z_attrib,
            show_flow=show_flow,
            angle=angle,
            label_size=label_size,
        )

        #plt.tight_layout() #Never worked anyway
        if save_as is not None:
            # plt.savefig(save_as, bbox_inches='tight')
            plt.savefig(save_as)
            plt.close()
        
        if show_plot is True:
            
            plt.show()
        

        return fig

    def network_explosion(
        self,
        save_as=None,
        show_plot=True,
        angle=250,
        networks=["all"],
        scaling_factor=1.5,
        dotted_lines=True,
    ):
        """Shows a plot of the network in 3d view

        Parameters
        ----------
        save_as : str
            optional parameter, string denoting full path and file name +
            extension for saving the plot
        show_plot : boolean
            True if the plot should be shown in the current Python instance,
            False if not
        angle : float
            View angle for 3d plot
        networks : list
            Instead of ['all'], the networks list can specify which networks
            should be plotted. Accepted items are {'heating', 'cooling',
            'electricity', 'gas', 'others'}
        scaling_factor : float
            Factor that scales the sized of node dots in the plot relative to
            the edge widths
        dotted_lines : boolean
            Optional dotted lines between different levels of network
            explosion if set to True

        Returns
        -------
        fig : matplotlib.figure.Figure
        """
        plt.rcParams["figure.figsize"] = 15, 15

        level_counter = 0
        z_step = 1

        fig = plt.figure()
        ax = plt.subplot(1, 1, 1, projection="3d")

        # Extract all necessary subgraphs
        building_graph = self.uesgraph.create_subgraphs(
            None, all_buildings=False, streets=True
        )["default"]
        heating_graphs = self.uesgraph.create_subgraphs("heating", all_buildings=False)
        cooling_graphs = self.uesgraph.create_subgraphs("cooling", all_buildings=False)
        electricity_graphs = self.uesgraph.create_subgraphs(
            "electricity", all_buildings=False
        )
        gas_graphs = self.uesgraph.create_subgraphs("gas", all_buildings=False)
        other_graphs = self.uesgraph.create_subgraphs("others", all_buildings=False)

        # Add first layer for whole uesgraph
        for node in self.uesgraph.nodelist_building:
            x = self.uesgraph.node[node]["position"].x
            y = self.uesgraph.node[node]["position"].y
            z = level_counter
            if self.uesgraph.node[node]["is_supply_heating"] is True:
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="#B22222",
                    edgecolors="#B22222",
                    s=scaling_factor * 2.5,
                    alpha=0.8,
                    depthshade=False,
                )
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="#6E8B3D",
                    edgecolors="#6E8B3D",
                    s=scaling_factor * 0.7,
                    alpha=0.7,
                    depthshade=False,
                )
            if self.uesgraph.node[node]["is_supply_cooling"] is True:
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="#1874CD",
                    edgecolors="#1874CD",
                    s=scaling_factor * 2.5,
                    alpha=0.8,
                    depthshade=False,
                )
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="green",
                    edgecolors="green",
                    s=scaling_factor * 0.7,
                    alpha=0.7,
                    depthshade=False,
                )
            elif self.uesgraph.node[node]["is_supply_electricity"] is True:
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="orange",
                    edgecolors="orange",
                    s=scaling_factor * 2.5,
                    alpha=0.8,
                    depthshade=False,
                )
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="green",
                    edgecolors="green",
                    s=scaling_factor * 0.7,
                    alpha=0.7,
                    depthshade=False,
                )
            elif self.uesgraph.node[node]["is_supply_gas"] is True:
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="grey",
                    edgecolors="grey",
                    s=scaling_factor * 2.5,
                    alpha=0.8,
                    depthshade=False,
                )
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="green",
                    edgecolors="green",
                    s=scaling_factor * 0.7,
                    alpha=0.7,
                    depthshade=False,
                )
            elif self.uesgraph.node[node]["is_supply_other"] is True:
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="purple",
                    edgecolors="purple",
                    s=scaling_factor * 2.5,
                    alpha=0.8,
                    depthshade=False,
                )
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="green",
                    edgecolors="green",
                    s=scaling_factor * 0.7,
                    alpha=0.7,
                    depthshade=False,
                )
            else:
                ax.scatter(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    c="#6E8B3D",
                    edgecolors="#6E8B3D",
                    s=scaling_factor,
                    alpha=0.8,
                    depthshade=False,
                )

        for edge in building_graph.edges():
            x = [
                self.uesgraph.node[edge[0]]["position"].x,
                self.uesgraph.node[edge[1]]["position"].x,
            ]
            y = [
                self.uesgraph.node[edge[0]]["position"].y,
                self.uesgraph.node[edge[1]]["position"].y,
            ]
            z = [level_counter, level_counter]
            ax.plot(x, y, zs=z, zdir="z", ls="-", color="grey", alpha=0.2, linewidth=2)
        for heating_graph in heating_graphs.values():
            for edge in heating_graph.edges():
                x = [
                    self.uesgraph.node[edge[0]]["position"].x,
                    self.uesgraph.node[edge[1]]["position"].x,
                ]
                y = [
                    self.uesgraph.node[edge[0]]["position"].y,
                    self.uesgraph.node[edge[1]]["position"].y,
                ]
                z = [level_counter, level_counter]
                ax.plot(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    ls="-",
                    color="#8B0000",
                    alpha=0.5,
                    linewidth=2,
                )
        for cooling_graph in cooling_graphs.values():
            for edge in cooling_graph.edges():
                x = [
                    self.uesgraph.node[edge[0]]["position"].x,
                    self.uesgraph.node[edge[1]]["position"].x,
                ]
                y = [
                    self.uesgraph.node[edge[0]]["position"].y,
                    self.uesgraph.node[edge[1]]["position"].y,
                ]
                z = [level_counter, level_counter]
                ax.plot(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    ls="-",
                    color="#1874CD",
                    alpha=0.5,
                    linewidth=2,
                )
        for electricity_graph in electricity_graphs.values():
            for edge in electricity_graph.edges():
                x = [
                    self.uesgraph.node[edge[0]]["position"].x,
                    self.uesgraph.node[edge[1]]["position"].x,
                ]
                y = [
                    self.uesgraph.node[edge[0]]["position"].y,
                    self.uesgraph.node[edge[1]]["position"].y,
                ]
                z = [level_counter, level_counter]
                ax.plot(
                    x, y, zs=z, zdir="z", ls="-", color="orange", alpha=0.5, linewidth=2
                )
        for gas_graph in gas_graphs.values():
            for edge in gas_graph.edges():
                x = [
                    self.uesgraph.node[edge[0]]["position"].x,
                    self.uesgraph.node[edge[1]]["position"].x,
                ]
                y = [
                    self.uesgraph.node[edge[0]]["position"].y,
                    self.uesgraph.node[edge[1]]["position"].y,
                ]
                z = [level_counter, level_counter]
                ax.plot(
                    x, y, zs=z, zdir="z", ls="-", color="grey", alpha=0.5, linewidth=2
                )
        for other_graph in other_graphs.values():
            for edge in other_graph.edges():
                x = [
                    self.uesgraph.node[edge[0]]["position"].x,
                    self.uesgraph.node[edge[1]]["position"].x,
                ]
                y = [
                    self.uesgraph.node[edge[0]]["position"].y,
                    self.uesgraph.node[edge[1]]["position"].y,
                ]
                z = [level_counter, level_counter]
                ax.plot(
                    x, y, zs=z, zdir="z", ls="-", color="purple", alpha=0.5, linewidth=2
                )

        level_counter += z_step

        # Add layer for heating networks
        if "all" in networks or "heating" in networks:
            if len(heating_graphs[list(heating_graphs.keys())[0]].nodes()) > 0:
                ax = self._add_network_layer_3d(
                    ax,
                    "heating",
                    level_counter,
                    scaling_factor,
                    dotted_lines=dotted_lines,
                )
                level_counter += z_step

        # Add layer for cooling networks
        if "all" in networks or "cooling" in networks:
            if len(cooling_graphs[list(cooling_graphs.keys())[0]].nodes()) > 0:
                ax = self._add_network_layer_3d(
                    ax,
                    "cooling",
                    level_counter,
                    scaling_factor,
                    dotted_lines=dotted_lines,
                )
                level_counter += z_step

        # Add layer for electricity networks
        if "all" in networks or "electricity" in networks:
            if electricity_graphs != {}:
                ax = self._add_network_layer_3d(
                    ax,
                    "electricity",
                    level_counter,
                    scaling_factor,
                    dotted_lines=dotted_lines,
                )
                level_counter += z_step

        # Add layer for gas networks
        if "all" in networks or "gas" in networks:
            if gas_graphs != {}:
                ax = self._add_network_layer_3d(
                    ax, "gas", level_counter, scaling_factor, dotted_lines=dotted_lines
                )
                level_counter += z_step

        # Add layer for other networks
        if "all" in networks or "others" in networks:
            if other_graphs != {}:
                ax = self._add_network_layer_3d(
                    ax,
                    "others",
                    level_counter,
                    scaling_factor,
                    dotted_lines=dotted_lines,
                )
                level_counter += z_step

        ax.view_init(20, angle)

        if level_counter > 1:
            ax.set_zlim([0.5, level_counter - 0.5])

        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_zticklabels([])

        ax.set_axis_off()

        if save_as is not None:
            plt.tight_layout()
            plt.savefig(save_as, bbox_inches="tight")
            plt.close()

        if show_plot is True:
            plt.tight_layout()
            plt.show()

        return fig

    def _add_network_layer_3d(
        self, ax, network_type, z_level, scaling_factor, dotted_lines, streets=False
    ):
        """Adds network of `network_type` to `z_level` of the plot in `ax`

        Parameters
        ----------
        ax : maplotlib ax object
        network_type : str
            Specifies the type of the destination network as {'heating',
            'cooling', 'electricity', 'gas', 'others'}
        z_level : float
            z-coordinate of new network layer
        scaling_factor : float
            Factor that scales the sized of node dots in the plot relative to
            the edge widths
        dotted_lines : boolean
            Optional dotted lines between different levels of network
            explosion if set to True
        streets : boolean
            Adds street edges to network layer representation if True

        Returns
        -------
        ax : maplotlib ax object
        """
        building_graph = self.uesgraph.create_subgraphs(
            None, all_buildings=False, streets=True
        )["default"]
        graph_dict = self.uesgraph.create_subgraphs(network_type, all_buildings=False)

        if network_type == "heating":
            network_color = "#8B0000"
        elif network_type == "cooling":
            network_color = "#1874CD"
        elif network_type == "electricity":
            network_color = "orange"
        elif network_type == "gas":
            network_color = "grey"
        elif network_type == "others":
            network_color = "purple"
            network_type = "other"

        for subgraph in graph_dict.values():
            if streets is True:
                for edge in building_graph.edges():
                    x = [
                        self.uesgraph.node[edge[0]]["position"].x,
                        self.uesgraph.node[edge[1]]["position"].x,
                    ]
                    y = [
                        self.uesgraph.node[edge[0]]["position"].y,
                        self.uesgraph.node[edge[1]]["position"].y,
                    ]
                    z = [z_level, z_level]
                    ax.plot(
                        x,
                        y,
                        zs=z,
                        zdir="z",
                        ls="-",
                        color="grey",
                        alpha=0.2,
                        linewidth=2,
                    )
            for edge in subgraph.edges():
                x = [
                    self.uesgraph.node[edge[0]]["position"].x,
                    self.uesgraph.node[edge[1]]["position"].x,
                ]
                y = [
                    self.uesgraph.node[edge[0]]["position"].y,
                    self.uesgraph.node[edge[1]]["position"].y,
                ]
                z = [z_level, z_level]
                ax.plot(
                    x,
                    y,
                    zs=z,
                    zdir="z",
                    ls="-",
                    color=network_color,
                    alpha=0.5,
                    linewidth=2,
                )

            for node in subgraph.nodes():
                x = self.uesgraph.node[node]["position"].x
                y = self.uesgraph.node[node]["position"].y
                z = z_level
                if "is_supply_other" in self.uesgraph.node[node]:
                    if self.uesgraph.node[node]["is_supply_" + network_type]:
                        ax.scatter(
                            x,
                            y,
                            zs=z,
                            zdir="z",
                            c=network_color,
                            edgecolors=network_color,
                            s=scaling_factor * 2.5,
                            alpha=0.8,
                            depthshade=False,
                        )
                        ax.scatter(
                            x,
                            y,
                            zs=z,
                            zdir="z",
                            c="green",
                            edgecolors="green",
                            s=scaling_factor * 0.7,
                            alpha=0.7,
                            depthshade=False,
                        )
                        if dotted_lines is True:
                            x = [x, x]
                            y = [y, y]
                            z = [0, z_level]
                            ax.plot(
                                x,
                                y,
                                zs=z,
                                zdir="z",
                                ls="dotted",
                                color=network_color,
                                alpha=0.7,
                                linewidth=2,
                            )
                    else:
                        ax.scatter(
                            x,
                            y,
                            zs=z,
                            zdir="z",
                            c="green",
                            edgecolors="green",
                            s=scaling_factor,
                            alpha=0.7,
                            depthshade=False,
                        )
                        if dotted_lines is True:
                            x = [x, x]
                            y = [y, y]
                            z = [0, z_level]
                            ax.plot(
                                x,
                                y,
                                zs=z,
                                zdir="z",
                                ls="dotted",
                                color="green",
                                alpha=0.4,
                                linewidth=2,
                            )
                else:
                    ax.scatter(
                        x,
                        y,
                        zs=z,
                        zdir="z",
                        c=network_color,
                        edgecolors=network_color,
                        s=scaling_factor * 0.5,
                        alpha=0.7,
                        depthshade=False,
                    )
        return ax

    def _add_node_marker(self, ax, nodelist, node_size=5, color="orange"):
        """Adds a special node marker to the building at `node_number`

        Parameters
        ----------
        ax : matplotlib ax object
            Marker will be added to this ax object.
            `uesgraphVis.create_plot(ax)` should be run on this ax beforehand.
        nodelist : list
            A list of node numbers
        node_size : float
            Size of the node marker
        color : str
            Color of the node marker

        Returns
        -------
        ax : maplotlib ax object
        """
        for building in nodelist:
            if self.uesgraph.node[building]["position"] is not None:
                ax.scatter(
                    self.uesgraph.node[building]["position"].x,
                    self.uesgraph.node[building]["position"].y,
                    s=node_size,
                    color=color,
                    alpha=0.7,
                )
        return ax

    def _add_edge_marker(self, ax, edge, color="orange"):
        """Adds a special edge marker

        Parameters
        ----------
        ax : matplotlib ax object
            Marker will be added to this ax object.
            `uesgraphVis.create_plot(ax)` should be run on this ax beforehand.
        edge : list
            A list of format [edge_0, edge_1]
        color : str
            Color of the node marker

        Returns
        -------
        ax : maplotlib ax object
        """
        nx.draw_networkx_edges(
            self.uesgraph,
            pos=self.uesgraph.positions,
            edgelist=[edge],
            edge_color=color,
            width=None,
        )
        return ax
    def _add_color_scale(self, ax1,minmax,ylabel, label_size,cmap = "viridis"):
        # ax1 = plt.subplot(gs[1])
        norm = Normalize(minmax[0],minmax[1])
        cb1 = mpl.colorbar.ColorbarBase(ax1, cmap=plt.get_cmap(cmap), norm=norm, orientation="vertical")
        cb1.ax.set_ylabel(ylabel, labelpad=15)
        text = cb1.ax.yaxis.label
        font = mpl.font_manager.FontProperties(size=label_size)
        text.set_font_properties(font)
        cb1.ax.tick_params(labelsize=label_size)
        

    def _paint_edges_extensive_sizes(self, ax,key,minmax,scaling_factor_diameter=25,zero_alpha=1,cmap = "viridis"):
        """
        Add the progression of extensive variables (e.g., mass flow) in color to the edges.

        This method visualizes the change in a specified variable along the edges of a graph
        using a constant color over an edge.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes object to which the plot additions will be made.
        key : str
            The string variable to access the desired edge variable.
            For example, "mass_flow" for plotting the mass flow.
        minmax : list of float
            A list containing the minimum and maximum values of the desired variable.
            Format: [minimum, maximum],
        scaling_factor_diameter : float
            Scaling factor for the edge diameter.
        zero_alpha : float
            The alpha channel value for the color of edges with a value close to the minimum value
            Useful to make pipes with same values transparent. For example if velocity deviations shall
            be plotted, the pipes with zero deviation can be made transparent to highlight smaller pipes
            with high deviations
        cmap : str, optional
            Name of the colormap to use for visualization (default='viridis').
            Common options include 'viridis', 'coolwarm', 'RdYlGn', 'plasma', 
            'Blues'. For temperature data, 'coolwarm' or 'RdYlGn' provide 
            intuitive red=hot, blue=cold color semantics.

        Returns
        -------
        matplotlib.axes.Axes
            The modified axes object with the added color-coded edges.

        Notes
        -----
        This method allows for generic definition, enabling the plotting of various units,
        that show a consant behavior over an edge, beyond just mass flow.
        """
        self.logger.debug(f"Scaling factor diameter extensive: {scaling_factor_diameter}")
        if minmax is None or minmax is False:
            minmax = self.uesgraph.get_min_max(key= key, mode = "edge")
        self.logger.debug(f"Minmax: {minmax}")
        
        #Create a colored block for every edge that get plotted on top of the network
        for edge in self.uesgraph.edges():
        #1 Extract geometric boundary conditions
            start = self.uesgraph.node[edge[0]]["position"]
            end = self.uesgraph.node[edge[1]]["position"]
            #start and end are POINT objects -> Transform to array thats readable for matplotlib
            line = np.array([(start.x, start.y), (end.x,end.y)])
            #define linewidth depending on diameter
            if "diameter" in self.uesgraph.edges[edge]:
                linewidth = ( self.uesgraph.edges[edge]["diameter"]) #only depending on diameter
            else:
                linewidth = 1
        #2 Get data of the edge
            try:
                value = self.uesgraph.edges[edge][key]
            except KeyError:
                raise KeyError(f"Edge {edge} has no {key}. Check assignment of {key} to edges")
            self.logger.debug(f"{key} found for {edge}: {value}")
        
        #3 Choose color from colormap-palette for the certain mass flow of the edge
            #3.1 Define alpha channel to make the color transparent if the value is close to zero
            eps = 1e-6
            if value < minmax[0] + eps:
                alpha_channel = zero_alpha
            else:
                alpha_channel = 1
            color = plt.get_cmap(cmap)(Normalize(minmax[0],minmax[1])(abs(value)),alpha_channel)
        
        #4 Summarize color and geometry to a LineCollection
            lc = LineCollection([line], colors=[color], linewidths=linewidth*scaling_factor_diameter)
        
        #5 Add LineCollection to the plot
            ax.add_collection(lc)
            
        #Miscellaneous
            #Funtionalities that were implemented in the old code and aren't migrated yet    
        #         if directions is True and add_flows is True:
        #         # Plot arrows for assumed flow direction
        #         for edge in self.uesgraph.edges():
        #             if "mass_flow" in self.uesgraph.edges[edge[0], edge[1]]:
        #                 mass_flow = self.uesgraph.edges[edge[0], edge[1]]["mass_flow"]
                     
        #             if mass_flow > 0:
        #                 pos_0 = self.uesgraph.node[edge[0]]["position"]
        #                 pos_1 = self.uesgraph.node[edge[1]]["position"]
        #             else:
        #                 pos_0 = self.uesgraph.node[edge[1]]["position"]
        #                 pos_1 = self.uesgraph.node[edge[0]]["position"]

        #             # center = (pos_0 + pos_1) / 2
        #             center = sg.LineString([pos_0, pos_1]).centroid
        #             x = float(center.x)
        #             y = float(center.y)
        #             dx = (float(pos_1.x - pos_0.x)) / 4
        #             dy = (float(pos_1.y - pos_0.y)) / 4

        #             ax.arrow(x, y, dx, dy, head_width=5, head_length=5, fc="k", ec="k")

        # if "problems" in self.uesgraph.graph:
        #     for node in self.uesgraph.graph["problems"]:
        #         ax.scatter(
        #             self.uesgraph.node[node]["position"].x,
        #             self.uesgraph.node[node]["position"].y,
        #             s=40,
        #             color="#1874CD",
        #             alpha=0.7,
        #         )
        #         ax.text(
        #             self.uesgraph.node[node]["position"].x,
        #             self.uesgraph.node[node]["position"].y,
        #             s=str(node),
        #             fontsize=4,
        #         )

    def _paint_edges_intensive_sizes(self, ax, key, minmax,scaling_factor_diameter=25,cmap = "viridis"):
        """
        Add the progression of intensive variables (e.g., temperature) in color to the edges.

        This method visualizes the change in a specified variable along the edges of a graph
        using a linear color gradient over an edge.

        Parameters
        ----------
        ax : matplotlib.axes.Axes
            The axes object to which the plot additions will be made.
        key : str
            The string variable to access the desired edge variable.
            For example, "temperature_supply" for plotting the temperature.
        minmax : list of float
            A list containing the minimum and maximum values of the desired variable.
            Format: [minimum, maximum]
        scaling_factor_diameter : float
            Scaling factor for the edge diameter.
        cmap : str, optional
            Name of the colormap to use for visualization (default='viridis').
            Common options include 'viridis', 'coolwarm', 'RdYlGn', 'plasma', 
            'Blues'. For temperature data, 'coolwarm' or 'RdYlGn' provide 
            intuitive red=hot, blue=cold color semantics.

        Returns
        -------
        matplotlib.axes.Axes
            The modified axes object with the added color-coded edges.

        Notes
        -----
        This method allows for generic definition, enabling the plotting of various units,
        that show a gradient over an edge, beyond just temperature.
        """
        self.logger.debug(f"Scaling factor diameter intensive: {scaling_factor_diameter}")
        
        if minmax is None or minmax is False:
            self.logger.debug("No minmax given. Calculating minmax")
            minmax = self.uesgraph.get_min_max(key = key, mode="node")
            self.logger.debug(f"Calculated minmax: {minmax}")
        self.logger.debug(f"Minmax: {minmax}")
        for edge in self.uesgraph.edges():
            #1 Extract geometric boundary conditions
            start = self.uesgraph.node[edge[0]]["position"]
            end = self.uesgraph.node[edge[1]]["position"]
            delta = start.distance(end)
            line = sg.LineString([start, end])

            #Define linewidh as depend on diameter only
            if "diameter" in self.uesgraph.edges[edge]:
                linewidth = ( self.uesgraph.edges[edge]["diameter"] ) #only depending on diameter
            else:
                linewidth = 1

            #2 Extract node values
            try:
                value_1 = self.uesgraph.nodes[edge[0]][key]
                value_2 = self.uesgraph.nodes[edge[1]][key]
            except KeyError:
                raise KeyError(f"Edge {self.uesgraph.nodes[edge[0]]} is missing {key}. Check assignment of {key} to edges")
            self.logger.debug(f"{key} found for {self.uesgraph.nodes[edge[0]]}: {value_1} and {self.uesgraph.nodes[edge[0]]}: {value_2}")

            #3 Define the size of discretization based on the amount of edes in network
            if len(self.uesgraph.edges()) < 25:
                discretization = 100
            else:
                discretization = 20

            #4 Create "discretization"-amount of points between value_1 and value_2
                #Basis for assigning a color to an edge segment
            color_vector = np.linspace(value_1, value_2, discretization)

            #5 Edge gets segmented in "discretization"-amount of intervalls
                #Those intervalls are gonna be painted in the color according    
            t = np.linspace(0, 1, discretization)
            x = []
            y = []
            for i in t:
                here = line.interpolate(delta * i)
                x.append(float(here.x))
                y.append(float(here.y))
            
            points = np.array([x, y]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)

            #6 Paint those segments
                #LineCollection with min-max values gets defined
            lc = LineCollection(
                    segments,
                    cmap=plt.get_cmap(cmap),
                    norm=Normalize(minmax[0], minmax[1]),
                )
                #Values like temperature get assigned to LineCollection which results 
                #   in a certain color depending on the min-max boundaries 
            lc.set_array(color_vector)

            #7 Set linewidth and add the Collection to the original plot
            lc.set_linewidth(linewidth * scaling_factor_diameter)
            ax.add_collection(lc)
    
    
    def _paint_edges_diameter(self, ax,scaling_factor_diameter=25):
        self.logger.debug(f"Scaling factor diameter paint diameter: {scaling_factor_diameter}")

        # Define a dictionary that maps diameter ranges to colors
        diameter_to_color = {
                    "DN20": 'brown',
                    "DN25": 'red',
                    "DN32": 'blue',
                    "DN40": 'green',
                    "DN50": 'yellow',
                    "DN65": 'purple',
                    "DN80": 'orange',
                    "DN100": 'pink',
                    "DN125": 'cyan',
                    "DN150": 'magenta',
                    "DN200": 'black',
    # Add more mappings as needed
                }

        def get_color(diameter):
            if 0.020 < diameter <= 0.023:
                return diameter_to_color["DN20"]
            elif 0.026 < diameter <= 0.028:
                return diameter_to_color["DN25"]
            elif 0.029 < diameter <= 0.037:
                return diameter_to_color["DN32"]
            elif 0.0407 <= diameter <= 0.043:
                return diameter_to_color["DN40"]
            elif 0.050 <= diameter <= 0.055:
                return diameter_to_color["DN50"]
            elif 0.065 <= diameter <= 0.071:
                return diameter_to_color["DN65"]
            elif 0.080 <= diameter <= 0.084:
                return diameter_to_color["DN80"]
            elif 0.095 <= diameter <= 0.108:
                return diameter_to_color["DN100"]
            elif 0.109 <= diameter <= 0.134:
                return diameter_to_color["DN125"]
            elif 0.140 <= diameter <= 0.187:
                return diameter_to_color["DN150"]
            elif 0.197 <= diameter <= 0.211:
                return diameter_to_color["DN200"]
            

            
        for edge in self.uesgraph.edges():
            if "diameter" in self.uesgraph.edges[edge[0], edge[1]]:
                diameter = self.uesgraph.edges[edge[0], edge[1]]["diameter"]
   
                # Get the color for the diameter
                color = get_color(diameter)
                x = [
                    self.uesgraph.node[edge[0]]["position"].x,
                    self.uesgraph.node[edge[1]]["position"].x,
                ]
                y = [
                    self.uesgraph.node[edge[0]]["position"].y,
                    self.uesgraph.node[edge[1]]["position"].y,
                ]
                
                ax.plot(x, y, ls="-", color=color, alpha=1, 
                        linewidth=diameter*scaling_factor_diameter,
                        solid_capstyle='butt',
                        zorder=1
                        )
                
        # Create a list of Line2D objects for the legend
        legend_lines = [mlines.Line2D([], [], color=color, lw=2) for color in diameter_to_color.values()]
        # Create a list of labels for the legend
        legend_labels = list(diameter_to_color.keys())

        # Add the legend to the plot
        ax.legend(legend_lines, legend_labels, loc='best')

        if "problems" in self.uesgraph.graph:
            for node in self.uesgraph.graph["problems"]:
                ax.scatter(
                    self.uesgraph.node[node]["position"].x,
                    self.uesgraph.node[node]["position"].y,
                    s=40,
                    color="#1874CD",
                    alpha=0.7,
                )
                ax.text(
                    self.uesgraph.node[node]["position"].x,
                    self.uesgraph.node[node]["position"].y,
                    s=str(node),
                    fontsize=4,
                )
