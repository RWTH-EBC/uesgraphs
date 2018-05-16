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


class Visuals(object):
    """
    Visualizes a uesgraph by networkX graph drawing

    Parameters
    ----------

    uesgraph : uesgraphs.uesgraph.UESGraph object
        The visualization output will be following the graph layout
        specified in the input uesgraph
    """

    def __init__(self, uesgraph):
        """
        Constructor for `Visuals`
        """
        self.uesgraph = uesgraph

    def create_plot_simple(self,
                           ax,
                           scaling_factor=0.5):
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
            ax.scatter(self.uesgraph.node[street]['position'].x,
                       self.uesgraph.node[street]['position'].y,
                       s=scaling_factor,
                       color='grey',
                       alpha=0.7)

        for nodelist_heating in list(self.uesgraph.nodelists_heating.values()):
            for heating_node in nodelist_heating:
                y_offset = random.choice([0.0001, 0.0002, 0.00015])
                x_offset = random.choice([0.0005, 0.00055, 0.0006, 0.00065,
                                          0.0007])
                ax.scatter(self.uesgraph.node[heating_node]['position'].x,
                           self.uesgraph.node[heating_node]['position'].y,
                           s=scaling_factor*15,
                           color='red',
                           alpha=0.7)

        for edge in self.uesgraph.edges():
            for node in edge:
                color = 'black'
                style = 'solid'
                alpha = 1
                linewidth=0.2
                if 'street' in self.uesgraph.node[node]['node_type']:
                    color = 'grey'
                    style = 'solid'
                    alpha = 0.7
                    linewidth=1.5
                    break
                elif 'heat' in self.uesgraph.node[node]['node_type']:
                    color = 'red'
                    style = 'solid'
                    linewidth=1
                    alpha = 1
                    break
                elif 'cool' in self.uesgraph.node[node]['node_type']:
                    color = 'blue'
                    style = 'solid'
                    linewidth=1
                    alpha = 1
                    break
            ax.plot([self.uesgraph.node[edge[0]]['position'].x,
                     self.uesgraph.node[edge[1]]['position'].x],
                    [self.uesgraph.node[edge[0]]['position'].y,
                     self.uesgraph.node[edge[1]]['position'].y],
                    color=color,
                    linewidth=linewidth,
                    alpha=alpha)

        for building in self.uesgraph.nodelist_building:
            if self.uesgraph.node[building]['position'] is not None:
                if self.uesgraph.node[building][
                        'is_supply_heating'] is False:
                    ax.scatter(self.uesgraph.node[building]['position'].x,
                               self.uesgraph.node[building]['position'].y,
                               s=scaling_factor * 3,
                               color='green',
                               alpha=0.7)
                else:
                    ax.scatter(self.uesgraph.node[building]['position'].x,
                               self.uesgraph.node[building]['position'].y,
                               s=scaling_factor * 25,
                               color='red',
                               alpha=0.7)
                counter += 1

        if 'proximity' in self.uesgraph.graph:
            try:
                poly = self.uesgraph.graph['proximity']
                x, y = poly.exterior.xy
                ax.plot(x, y, color='red', alpha=0.7,
                        linewidth=1, solid_capstyle='round', zorder=2)
            except:
                None

        plt.tick_params(axis='both',
                        which='both',
                        bottom=False,
                        top=False,
                        labelbottom=False,
                        right=False,
                        left=False,
                        labelleft=False)

        plt.axis('equal')
        ax.get_xaxis().get_major_formatter().set_useOffset(False)
        ax.axis('off')

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
            warnings.warn('The placement of elements in versions older than'
                          'Python 3.6 may differ from the 3.6 placement')

        diagonal = self.uesgraph.max_position.distance(
            self.uesgraph.min_position)
        curr_scaling = diagonal * 0.04

        if isinstance(element, tuple):
            edge = element
            pos_0 = self.uesgraph.node[edge[0]]['position']
            pos_1 = self.uesgraph.node[edge[1]]['position']

            parallel_line = sg.LineString([pos_0, pos_1]).parallel_offset(
                curr_scaling/2)
            text_pos = sg.Point(parallel_line.centroid.x,
                                parallel_line.centroid.y-curr_scaling/4.)

        else:
            node = element

            node_pos = self.uesgraph.node[node]['position']
            neighbors = list(self.uesgraph.neighbors(node))
            if len(neighbors) > 1:
                # Find 2 nearest neighbors `neighbor_0` and `neighbor_1`
                distances = {}
                for neighbor in neighbors:
                    neighbor_pos= self.uesgraph.node[neighbor]['position']
                    distances[neighbor] = neighbor_pos.distance(node_pos)
                neighbor_0 = min(distances, key=distances.get)
                del distances[neighbor_0]
                neighbor_1 = min(distances, key=distances.get)

                neighbor_0_pos = self.uesgraph.node[neighbor_0]['position']
                neighbor_1_pos = self.uesgraph.node[neighbor_1]['position']


                # Find `ref_point` between both nearest neighbors
                ref_point = sg.LineString([neighbor_0_pos,
                                           neighbor_1_pos]).centroid

                # Place text on line between `ref_point` and `node`
                # text_pos = sg.LineString([node_pos, ref_point]).interpolate(
                #     curr_scaling)
                text_pos = ref_point
                plt.plot([ref_point.x, node_pos.x],
                         [ref_point.y, node_pos.y],
                         '--',
                         color='black',
                         alpha=0.7)
            else:
                neighbor_pos = self.uesgraph.node[neighbors[0]]['position']

                dx = node_pos.x - neighbor_pos.x
                dy = node_pos.y - neighbor_pos.y
                opposite = sg.Point(node_pos.x + dx,
                                    node_pos.y + dy)

                ring_distance = curr_scaling

                text_pos = node_pos.buffer(ring_distance).exterior.intersection(
                    sg.LineString([node_pos, opposite]))

        return text_pos

    def create_plot(self,
                    ax,
                    labels=None,
                    show_diameters=False,
                    show_mass_flows=False,
                    label_size=7,
                    edge_markers=[],
                    node_markers=[],
                    add_edge_temperatures=False,
                    add_edge_flows=False,
                    directions=False,
                    scaling_factor=1.5,
                    scaling_factor_diameter=25,
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

        Returns
        -------
        ax : maplotlib ax object
        """
        assert show_diameters is False or show_mass_flows is False

        if show_mass_flows is True:
            mass_flow_max = 0
            volume_flows = [0]
            for edge in self.uesgraph.edges():
                if 'mass_flow' in self.uesgraph.edges[edge[0], edge[1]]:
                    curr_m = abs(self.uesgraph.edges[
                        edge[0], edge[1]]['mass_flow'])
                    if curr_m > mass_flow_max:
                        mass_flow_max = curr_m
                if 'volume_flow' in self.uesgraph.edges[edge[0], edge[1]]:
                    volume_flows.append(abs(self.uesgraph.edges[
                        edge[0], edge[1]]['volume_flow']))

            volume_flow_max = max(volume_flows)

        for street in self.uesgraph.nodelist_street:
            draw = nx.draw_networkx_nodes(self.uesgraph,
                                          pos=self.uesgraph.positions,
                                          nodelist=[street],
                                          node_size=2 * scaling_factor,
                                          node_color='black',
                                          linewidths=None,
                                          alpha=0.2
                                          )
            if labels == 'street':
                plt.text(self.uesgraph.node[street]['position'].x,
                         self.uesgraph.node[street]['position'].y,
                         s=str(street),
                         horizontalalignment='center',
                         fontsize=label_size)
            if draw is not None:
                draw.set_edgecolor('black')

        for heat_network in self.uesgraph.nodelists_heating.keys():
            for node in self.uesgraph.nodelists_heating[heat_network]:
                draw = nx.draw_networkx_nodes(self.uesgraph,
                                              pos=self.uesgraph.positions,
                                              nodelist=[node],
                                              node_color='red',
                                              node_size=3 * scaling_factor,
                                              linewidths=None,
                                              alpha=0.7)
                if labels == 'heat':
                    plt.text(self.uesgraph.node[node]['position'].x,
                             self.uesgraph.node[node]['position'].y,
                             s=str(node),
                             horizontalalignment='center',
                             fontsize=label_size)
                if labels == 'name':
                    if 'name' in self.uesgraph.node[node]:
                        text_pos = self._place_text(node)
                        plt.text(text_pos.x,
                                 text_pos.y,
                                 s=str(self.uesgraph.node[node]['name']),
                                 horizontalalignment='center',
                                 fontsize=label_size)
                if draw is not None:
                    draw.set_edgecolor('red')
        for cool_network in self.uesgraph.nodelists_cooling.keys():
            for node in self.uesgraph.nodelists_cooling[cool_network]:
                draw = nx.draw_networkx_nodes(self.uesgraph,
                                              pos=self.uesgraph.positions,
                                              nodelist=[node],
                                              node_color='blue',
                                              node_size=1,
                                              linewidths=None,
                                              alpha=0.7)
                if draw is not None:
                    draw.set_edgecolor('blue')
        for elec_network in self.uesgraph.nodelists_electricity.keys():
            for node in self.uesgraph.nodelists_electricity[elec_network]:
                draw = nx.draw_networkx_nodes(self.uesgraph,
                                              pos=self.uesgraph.positions,
                                              nodelist=[node],
                                              node_color='orange',
                                              node_size=3 * scaling_factor,
                                              linewidths=None)
                if draw is not None:
                    draw.set_edgecolor('orange')
        for gas_network in self.uesgraph.nodelists_gas.keys():
            for node in self.uesgraph.nodelists_gas[gas_network]:
                draw = nx.draw_networkx_nodes(self.uesgraph,
                                              pos=self.uesgraph.positions,
                                              nodelist=[node],
                                              node_color='gray',
                                              node_size=3 * scaling_factor,
                                              linewidths=None)
                if draw is not None:
                    draw.set_edgecolor('gray')
        for other_network in self.uesgraph.nodelists_others.keys():
            for node in self.uesgraph.nodelists_others[other_network]:
                draw = nx.draw_networkx_nodes(self.uesgraph,
                                              pos=self.uesgraph.positions,
                                              nodelist=[node],
                                              node_color='purple',
                                              node_size=3 * scaling_factor,
                                              linewidths=None)
                if draw is not None:
                    draw.set_edgecolor('purple')

        for building in self.uesgraph.nodelist_building:
            if self.uesgraph.node[building]['position'] is not None:
                if self.uesgraph.node[building]['is_supply_heating'] is True:
                    draw = nx.draw_networkx_nodes(self.uesgraph,
                                                  pos=self.uesgraph.positions,
                                                  nodelist=[building],
                                                  node_color='red',
                                                  node_size=90 *
                                                  scaling_factor,
                                                  linewidths=None)
                    if draw is not None:
                        draw.set_edgecolor('red')
                if self.uesgraph.node[building]['is_supply_cooling'] is True:
                    draw = nx.draw_networkx_nodes(self.uesgraph,
                                                  pos=self.uesgraph.positions,
                                                  nodelist=[building],
                                                  node_color='blue',
                                                  node_size=60 *
                                                  scaling_factor,
                                                  linewidths=None)
                    if draw is not None:
                        draw.set_edgecolor('blue')
                if self.uesgraph.node[building]['is_supply_gas'] is True:
                    draw = nx.draw_networkx_nodes(self.uesgraph,
                                                  pos=self.uesgraph.positions,
                                                  nodelist=[building],
                                                  node_color='gray',
                                                  node_size=40 *
                                                  scaling_factor,
                                                  linewidths=None)
                    if draw is not None:
                        draw.set_edgecolor('gray')

                draw = nx.draw_networkx_nodes(self.uesgraph,
                                              pos=self.uesgraph.positions,
                                              nodelist=[building],
                                              node_size=25 * scaling_factor,
                                              node_color='green',
                                              linewidths=None,
                                              alpha=0.7
                                              )
                if labels == 'building':
                    plt.text(self.uesgraph.node[building]['position'].x,
                             self.uesgraph.node[building]['position'].y,
                             s=str(building),
                             horizontalalignment='center',
                             fontsize=label_size)
                elif labels == 'name':
                    if 'name' in self.uesgraph.node[building]:
                        text_pos = self._place_text(building)
                        plt.text(text_pos.x,
                                 text_pos.y,
                                 s=self.uesgraph.node[building]['name'],
                                 horizontalalignment='center',
                                 fontsize=label_size)
                if draw is not None:
                    draw.set_edgecolor('green')

                if self.uesgraph.node[building][
                        'is_supply_electricity'] is True:
                    draw = nx.draw_networkx_nodes(self.uesgraph,
                                                  pos=self.uesgraph.positions,
                                                  nodelist=[building],
                                                  node_color='orange',
                                                  node_size=12 *
                                                  scaling_factor,
                                                  linewidths=None,
                                                  alpha=0.8)
                    if draw is not None:
                        draw.set_edgecolor('orange')
                if self.uesgraph.node[building]['is_supply_other'] is True:
                    draw = nx.draw_networkx_nodes(self.uesgraph,
                                                  pos=self.uesgraph.positions,
                                                  nodelist=[building],
                                                  node_color='purple',
                                                  node_size=5 *
                                                  scaling_factor,
                                                  linewidths=None,
                                                  alpha=0.5)
                    if draw is not None:
                        draw.set_edgecolor('purple')

        for edge in self.uesgraph.edges():
            for node in edge:
                color = 'black'
                style = 'solid'
                alpha = 1

                if show_diameters is True:
                    if 'diameter' in self.uesgraph.edges[
                            edge[0], edge[1]]:
                        weight = self.uesgraph.edges[edge[0], edge[1]][
                                     'diameter'] * scaling_factor_diameter
                    else:
                        weight = 0.01
                elif show_mass_flows is True:
                    if 'mass_flow' in self.uesgraph.edges[
                            edge[0], edge[1]]:
                        weight = abs(self.uesgraph.edges[edge[0], edge[1]][
                                         'mass_flow']) / mass_flow_max * 10
                    elif 'volume_flow' in self.uesgraph.edge[
                            edge[0]][edge[1]]:
                        weight = abs(self.uesgraph.edges[edge[0], edge[1]][
                                         'volume_flow']) / volume_flow_max * 10
                        if weight < 0.5 and self.uesgraph.edges[edge[0],
                                                                edge[1]][
                            'volume_flow'] > 1e-9:
                            weight = 10.5
                    else:
                        weight = 0.01

                if 'street' in self.uesgraph.node[node]['node_type']:
                    color = 'black'
                    style = 'solid'
                    alpha = 0.2
                    break
                elif 'heat' in self.uesgraph.node[node]['node_type']:
                    color = 'red'
                    style = 'solid'
                    alpha = 0.8
                    break
                elif 'cool' in self.uesgraph.node[node]['node_type']:
                    color = 'blue'
                    style = 'solid'
                    alpha = 0.8
                    break
                elif 'elec' in self.uesgraph.node[node]['node_type']:
                    color = 'orange'
                    style = 'dotted'
                    alpha = 0.8
                    break
                elif 'gas' in self.uesgraph.node[node]['node_type']:
                    color = 'gray'
                    style = 'dashdot'
                    alpha = 0.8
                    break
                elif 'others' in self.uesgraph.node[node]['node_type']:
                    color = 'purple'
                    style = 'dashdot'
                    alpha = 0.8
                    break

            if show_diameters is True or show_mass_flows is True:
                nx.draw_networkx_edges(self.uesgraph,
                                       pos=self.uesgraph.positions,
                                       edgelist=[edge],
                                       style=style,
                                       width=weight,
                                       edge_color=[color],
                                       alpha=alpha)
            else:
                nx.draw_networkx_edges(self.uesgraph,
                                       pos=self.uesgraph.positions,
                                       edgelist=[edge],
                                       style=style,
                                       edge_color=[color],
                                       alpha=alpha)
            if labels == 'name':
                if 'name' in self.uesgraph.edges[edge[0], edge[1]]:
                    text_pos = self._place_text(edge)
                    plt.text(text_pos.x,
                             text_pos.y,
                             s=self.uesgraph.edges[edge[0], edge[1]]['name'],
                             horizontalalignment='center',
                             fontsize=label_size)

        if labels == 'all_nodes':
            for node in self.uesgraph.nodes():
                plt.text(self.uesgraph.node[node]['position'].x,
                         self.uesgraph.node[node]['position'].y,
                         s=str(node),
                         horizontalalignment='center',
                         fontsize=label_size)

        if add_edge_temperatures is True or add_edge_flows is True:
            self._add_edge_data(ax,
                                add_temperatures=add_edge_temperatures,
                                add_flows=add_edge_flows,
                                directions=directions)

        for edge in edge_markers:
            self._add_edge_marker(ax, edge)
        if node_markers != []:
            self._add_node_marker(
                ax,
                node_markers,
                node_size=50*scaling_factor,
            )

        if directions is True and add_edge_flows is False:
            # Plot arrows for assumed flow direction
            for edge in self.uesgraph.edges():
                pos_0 = self.uesgraph.node[edge[0]]['position']
                pos_1 = self.uesgraph.node[edge[1]]['position']
                # center = (pos_0 + pos_1) / 2
                center = sg.LineString([pos_0, pos_1]).centroid
                arrow_head = center.distance(pos_0) / 10
                x = float(center.x)
                y = float(center.y)
                dx = (float(pos_1.x - pos_0.x)) / 4
                dy = (float(pos_1.y - pos_0.y)) / 4

                ax.arrow(x, y, dx, dy,
                         head_width=arrow_head, head_length=arrow_head,
                         linewidth=1,
                         fc='k', ec='k')

        plt.tick_params(axis='both',
                        which='both',
                        bottom=False,
                        top=False,
                        labelbottom=False,
                        right=False,
                        left=False,
                        labelleft=False)

        plt.axis('equal')
        ax.get_xaxis().get_major_formatter().set_useOffset(False)
        ax.axis('off')

        return ax

    def create_plot_3d(self,
                       ax,
                       z_attrib='pressure',
                       show_flow=False,
                       angle=110,
                       label_size=20,
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
                flows.append(self.uesgraph.edge[
                                 edge[0]][edge[1]]['volume_flow'])
            min_flow = min(flows)
            max_flow = max(flows)
            delta_flow = max_flow - min_flow

            for edge in self.uesgraph.edges():
                flow = self.uesgraph.edge[edge[0]][edge[1]]['volume_flow']
                weight = ((flow - min_flow) / delta_flow) * 3
                print('weight', weight)
                self.uesgraph.edge[edge[0]][edge[1]]['weight'] = weight + 0.1

        for node in self.uesgraph.nodes():
            if z_attrib in self.uesgraph.node[node]:
                x = self.uesgraph.node[node]['position'].x
                y = self.uesgraph.node[node]['position'].y
                z = self.uesgraph.node[node][z_attrib] * 1e-5
                ax.scatter(x, y, zs=z, zdir='z', c='0.5', alpha=0.5)

        for edge in self.uesgraph.edges():
            if (z_attrib in self.uesgraph.node[edge[0]] and
                    z_attrib in self.uesgraph.node[edge[1]]):
                x = [self.uesgraph.node[edge[0]]['position'].x,
                     self.uesgraph.node[edge[1]]['position'].x]
                y = [self.uesgraph.node[edge[0]]['position'].y,
                     self.uesgraph.node[edge[1]]['position'].y]
                z = [self.uesgraph.node[edge[0]][z_attrib] * 1e-5,
                     self.uesgraph.node[edge[1]][z_attrib] * 1e-5]
                if show_flow is False:
                    ax.plot(x, y, zs=z, zdir='z', ls='-', color='grey',
                            alpha=0.5)
                else:
                    linewidth = self.uesgraph.edge[edge[0]][edge[1]]['weight']
                    ax.plot(x, y, zs=z, zdir='z', ls='-', color='grey',
                            alpha=0.5, linewidth=linewidth)
        for node in self.uesgraph.nodes():
            if 'is_supply_heating' in self.uesgraph.node[node]:
                if self.uesgraph.node[node]['is_supply_heating']:
                    x = self.uesgraph.node[node]['position'].x
                    y = self.uesgraph.node[node]['position'].y
                    z = self.uesgraph.node[node][z_attrib] * 1e-5
                    ax.scatter(x, y, zs=z, zdir='z', c='red')

        ax.view_init(20, angle)
        ax.set_zlabel('Pressure in bar', fontsize=label_size,
                      labelpad=label_size*2)
        ax.tick_params(labelsize=label_size, pad=label_size)

        ax.set_xticklabels([])
        ax.set_yticklabels([])

        return ax

    def show_network(self,
                     save_as=None,
                     show_plot=True,
                     labels=None,
                     show_diameters=False,
                     show_mass_flows=False,
                     label_size=7,
                     edge_markers=[],
                     node_markers=[],
                     add_edge_temperatures=False,
                     add_edge_flows=False,
                     directions=False,
                     scaling_factor=1.5,
                     scaling_factor_diameter=25,
                     simple=False,):
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
        simple : boolean
            For very large uesgraphs, the standard plotting may take too long
            (hours...). In these cases, `simple=True` gives faster results
        """
        dx = float(self.uesgraph.max_position.x - self.uesgraph.min_position.x)
        dy = float(self.uesgraph.max_position.y - self.uesgraph.min_position.y)

        if self.uesgraph.max_position.x == self.uesgraph.min_position.x:
            dx = 1
        if self.uesgraph.max_position.y == self.uesgraph.min_position.y:
            dy = 1

        if dx >= dy:
            x_size = 20
            y_size = x_size * dy/dx
        else:
            y_size = 20
            x_size = y_size * dx/dy

        plt.rcParams['figure.figsize'] = x_size, y_size

        fig = plt.figure()
        if add_edge_temperatures is True:
            gs = gridspec.GridSpec(1, 2,
                                   width_ratios=[20, 1])
            ax = plt.subplot(gs[0])

        else:
            ax = plt.subplot(1, 1, 1)

        if simple is False:
            ax = self.create_plot(
                ax,
                labels=labels,
                show_diameters=show_diameters,
                show_mass_flows=show_mass_flows,
                label_size=label_size,
                edge_markers=edge_markers,
                node_markers=node_markers,
                add_edge_temperatures=add_edge_temperatures,
                add_edge_flows=add_edge_flows,
                directions=directions,
                scaling_factor=scaling_factor,
                scaling_factor_diameter=scaling_factor_diameter,
            )
        else:
            ax = self.create_plot_simple(
                ax,
                scaling_factor=scaling_factor,
            )

        margin_x = dx/20
        margin_y = dy/20
        ax.set_xlim([float(self.uesgraph.min_position.x) - margin_x,
                     float(self.uesgraph.max_position.x) + margin_x])
        ax.set_ylim([float(self.uesgraph.min_position.y) - margin_y,
                     float(self.uesgraph.max_position.y) + margin_y])

        if add_edge_temperatures is True:
            temperatures = []
            for node in self.uesgraph.nodes():
                if 'temperature_supply' in self.uesgraph.node[node]:
                    temperatures.append(self.uesgraph.node[node][
                                            'temperature_supply'])
                    print(node, self.uesgraph.node[node][
                        'temperature_supply'])
            mean_temperature = np.mean(temperatures)
            std_temperatures = np.std(temperatures)
            temperature_min = max(min(temperatures),
                                  mean_temperature - 2 * std_temperatures)
            temperature_max = min(max(temperatures),
                                  mean_temperature + 2 * std_temperatures)

            print('temperature_min for colormap', temperature_min)
            print('temperature_max for colormap', temperature_max)

            ax1 = plt.subplot(gs[1])
            norm = mpl.colors.Normalize(vmin=temperature_min,
                                        vmax=temperature_max)
            cb1 = mpl.colorbar.ColorbarBase(ax1,
                                            cmap=plt.get_cmap('viridis'),
                                            norm=norm,
                                            orientation='vertical'
                                            )
            cb1.ax.set_ylabel(u'Temperature in °C', labelpad=15)
            text = cb1.ax.yaxis.label
            font = matplotlib.font_manager.FontProperties(size=label_size)
            text.set_font_properties(font)
            cb1.ax.tick_params(labelsize=label_size)

            # The following work-around tries to make sure that the
            # ticklabels are not obscured by some strange offset behaviour
            ticklabels = [float(item.get_text()) for item in
                          cb1.ax.get_yticklabels()]

            # Calculate new ticklabels
            dT = temperature_max - temperature_min
            step = dT / (len(ticklabels) + 1)

            new_ticklabels = []
            for i in range(len(ticklabels)):
                base_temperature = temperature_min
                if temperature_min - 273.15 > 0:
                    base_temperature -= 273.15

                if step > 1:
                    decimals = 0
                elif step > 0.1:
                    decimals = 1
                else:
                    decimals = 2

                new_ticklabels.append(round(base_temperature+step*(i+1),
                                            decimals))

            cb1.ax.set_yticklabels(new_ticklabels)

        if save_as is not None:
            plt.savefig(save_as, bbox_inches='tight', dpi=150)
            plt.close()

        if show_plot is True:
            plt.show()

        return fig


    def show_3d(self,
                save_as=None,
                show_plot=True,
                show_flow=False,
                z_attrib='pressure',
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
        angle : float
            View angle for 3d plot
        label_size : int
            Fontsize for optional labels
        """
        plt.rcParams['figure.figsize'] = 10, 10

        fig = plt.figure()
        ax = plt.subplot(1, 1, 1, projection='3d')

        ax = self.create_plot_3d(ax, z_attrib=z_attrib, show_flow=show_flow,
                                 angle=angle, label_size=label_size)

        # plt.tight_layout()
        if save_as is not None:
            # plt.savefig(save_as, bbox_inches='tight')
            plt.savefig(save_as)
            plt.close()

        if show_plot is True:
            plt.show()

        return fig

    def network_explosion(self,
                          save_as=None,
                          show_plot=True,
                          angle=250,
                          networks=['all'],
                          scaling_factor=1.5,
                          dotted_lines=True):
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
        """
        plt.rcParams['figure.figsize'] = 15, 15

        level_counter = 0
        z_step = 1

        fig = plt.figure()
        ax = plt.subplot(1, 1, 1, projection='3d')

        # Extract all necessary subgraphs
        building_graph = self.uesgraph.create_subgraphs(None,
                                                        all_buildings=False,
                                                        streets=True)[
                                                            'default']
        heating_graphs = self.uesgraph.create_subgraphs('heating',
                                                        all_buildings=False)
        cooling_graphs = self.uesgraph.create_subgraphs('cooling',
                                                        all_buildings=False)
        electricity_graphs = self.uesgraph.create_subgraphs('electricity',
                                                        all_buildings=False)
        gas_graphs = self.uesgraph.create_subgraphs('gas',
                                                    all_buildings=False)
        other_graphs = self.uesgraph.create_subgraphs('others',
                                                      all_buildings=False)

        # Add first layer for whole uesgraph
        for node in self.uesgraph.nodelist_building:
            x = self.uesgraph.node[node]['position'].x
            y = self.uesgraph.node[node]['position'].y
            z = level_counter
            if self.uesgraph.node[node]['is_supply_heating'] is True:
                ax.scatter(x, y, zs=z, zdir='z',
                           c='red', edgecolors='red',
                           s=scaling_factor*2.5,
                           alpha=0.8,
                           depthshade=False)
                ax.scatter(x, y, zs=z, zdir='z',
                           c='green', edgecolors='green',
                           s=scaling_factor*0.7,
                           alpha=0.7,
                           depthshade=False)
            elif self.uesgraph.node[node]['is_supply_cooling'] is True:
                ax.scatter(x, y, zs=z, zdir='z',
                           c='blue', edgecolors='blue',
                           s=scaling_factor*2.5,
                           alpha=0.8,
                           depthshade=False)
                ax.scatter(x, y, zs=z, zdir='z',
                           c='green', edgecolors='green',
                           s=scaling_factor*0.7,
                           alpha=0.7,
                           depthshade=False)
            elif self.uesgraph.node[node]['is_supply_electricity'] is True:
                ax.scatter(x, y, zs=z, zdir='z',
                           c='orange', edgecolors='orange',
                           s=scaling_factor*2.5,
                           alpha=0.8,
                           depthshade=False)
                ax.scatter(x, y, zs=z, zdir='z',
                           c='green', edgecolors='green',
                           s=scaling_factor*0.7,
                           alpha=0.7,
                           depthshade=False)
            elif self.uesgraph.node[node]['is_supply_gas'] is True:
                ax.scatter(x, y, zs=z, zdir='z',
                           c='grey', edgecolors='grey',
                           s=scaling_factor*2.5,
                           alpha=0.8,
                           depthshade=False)
                ax.scatter(x, y, zs=z, zdir='z',
                           c='green', edgecolors='green',
                           s=scaling_factor*0.7,
                           alpha=0.7,
                           depthshade=False)
            elif self.uesgraph.node[node]['is_supply_other'] is True:
                ax.scatter(x, y, zs=z, zdir='z',
                           c='purple', edgecolors='purple',
                           s=scaling_factor*2.5,
                           alpha=0.8,
                           depthshade=False)
                ax.scatter(x, y, zs=z, zdir='z',
                           c='green', edgecolors='green',
                           s=scaling_factor*0.7,
                           alpha=0.7,
                           depthshade=False)
            else:
                ax.scatter(x, y, zs=z, zdir='z',
                           c='green', edgecolors='green',
                           s=scaling_factor,
                           alpha=0.8,
                           depthshade=False)

        for edge in building_graph.edges():
            x = [self.uesgraph.node[edge[0]]['position'].x,
                 self.uesgraph.node[edge[1]]['position'].x]
            y = [self.uesgraph.node[edge[0]]['position'].y,
                 self.uesgraph.node[edge[1]]['position'].y]
            z = [level_counter, level_counter]
            ax.plot(x, y, zs=z, zdir='z', ls='-', color='grey',
                    alpha=0.2, linewidth=2)
        for heating_graph in heating_graphs.values():
            for edge in heating_graph.edges():
                x = [self.uesgraph.node[edge[0]]['position'].x,
                     self.uesgraph.node[edge[1]]['position'].x]
                y = [self.uesgraph.node[edge[0]]['position'].y,
                     self.uesgraph.node[edge[1]]['position'].y]
                z = [level_counter, level_counter]
                ax.plot(x, y, zs=z, zdir='z', ls='-', color='red',
                        alpha=0.5, linewidth=2)
        for cooling_graph in cooling_graphs.values():
            for edge in cooling_graph.edges():
                x = [self.uesgraph.node[edge[0]]['position'].x,
                     self.uesgraph.node[edge[1]]['position'].x]
                y = [self.uesgraph.node[edge[0]]['position'].y,
                     self.uesgraph.node[edge[1]]['position'].y]
                z = [level_counter, level_counter]
                ax.plot(x, y, zs=z, zdir='z', ls='-', color='blue',
                        alpha=0.5, linewidth=2)
        for electricity_graph in electricity_graphs.values():
            for edge in electricity_graph.edges():
                x = [self.uesgraph.node[edge[0]]['position'].x,
                     self.uesgraph.node[edge[1]]['position'].x]
                y = [self.uesgraph.node[edge[0]]['position'].y,
                     self.uesgraph.node[edge[1]]['position'].y]
                z = [level_counter, level_counter]
                ax.plot(x, y, zs=z, zdir='z', ls='-', color='orange',
                        alpha=0.5, linewidth=2)
        for gas_graph in gas_graphs.values():
            for edge in gas_graph.edges():
                x = [self.uesgraph.node[edge[0]]['position'].x,
                     self.uesgraph.node[edge[1]]['position'].x]
                y = [self.uesgraph.node[edge[0]]['position'].y,
                     self.uesgraph.node[edge[1]]['position'].y]
                z = [level_counter, level_counter]
                ax.plot(x, y, zs=z, zdir='z', ls='-', color='grey',
                        alpha=0.5, linewidth=2)
        for other_graph in other_graphs.values():
            for edge in other_graph.edges():
                x = [self.uesgraph.node[edge[0]]['position'].x,
                     self.uesgraph.node[edge[1]]['position'].x]
                y = [self.uesgraph.node[edge[0]]['position'].y,
                     self.uesgraph.node[edge[1]]['position'].y]
                z = [level_counter, level_counter]
                ax.plot(x, y, zs=z, zdir='z', ls='-', color='purple',
                        alpha=0.5, linewidth=2)

        level_counter += z_step

        # Add layer for heating networks
        if 'all' in networks or 'heating' in networks:
            if len(heating_graphs[list(heating_graphs.keys())[0]].nodes()) > 0:
                ax = self._add_network_layer_3d(ax, 'heating',
                                                level_counter,
                                                scaling_factor,
                                                dotted_lines=dotted_lines)
                level_counter += z_step

        # Add layer for cooling networks
        if 'all' in networks or 'cooling' in networks:
            if len(cooling_graphs[list(cooling_graphs.keys())[0]].nodes()) > 0:
                ax = self._add_network_layer_3d(ax, 'cooling',
                                                level_counter,
                                                scaling_factor,
                                                dotted_lines=dotted_lines)
                level_counter += z_step

        # Add layer for electricity networks
        if 'all' in networks or 'electricity' in networks:
            if electricity_graphs != {}:
                ax = self._add_network_layer_3d(ax, 'electricity',
                                                level_counter,
                                                scaling_factor,
                                                dotted_lines=dotted_lines)
                level_counter += z_step

        # Add layer for gas networks
        if 'all' in networks or 'gas' in networks:
            if gas_graphs != {}:
                ax = self._add_network_layer_3d(ax, 'gas',
                                                level_counter,
                                                scaling_factor,
                                                dotted_lines=dotted_lines)
                level_counter += z_step

        # Add layer for other networks
        if 'all' in networks or 'others' in networks:
            if other_graphs != {}:
                ax = self._add_network_layer_3d(ax, 'others',
                                                level_counter,
                                                scaling_factor,
                                                dotted_lines=dotted_lines)
                level_counter += z_step

        ax.view_init(20, angle)

        if level_counter > 1:
            ax.set_zlim([0.5, level_counter-0.5])

        ax.set_xticklabels([])
        ax.set_yticklabels([])
        ax.set_zticklabels([])

        ax.set_axis_off()

        if save_as is not None:
            plt.tight_layout()
            plt.savefig(save_as, bbox_inches='tight')
            plt.close()

        if show_plot is True:
            plt.tight_layout()
            plt.show()

        return fig


    def _add_network_layer_3d(self, ax, network_type, z_level,
                              scaling_factor, dotted_lines, streets=False):
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
        building_graph = self.uesgraph.create_subgraphs(None,
                                                        all_buildings=False,
                                                        streets=True)[
                                                            'default']
        graph_dict = self.uesgraph.create_subgraphs(network_type,
                                                    all_buildings=False)

        if network_type == 'heating':
            network_color = 'red'
        elif network_type == 'cooling':
            network_color = 'blue'
        elif network_type == 'electricity':
            network_color = 'orange'
        elif network_type == 'gas':
            network_color = 'grey'
        elif network_type == 'others':
            network_color = 'purple'
            network_type = 'other'

        for subgraph in graph_dict.values():
            if streets is True:
                for edge in building_graph.edges():
                    x = [self.uesgraph.node[edge[0]]['position'].x,
                         self.uesgraph.node[edge[1]]['position'].x]
                    y = [self.uesgraph.node[edge[0]]['position'].y,
                         self.uesgraph.node[edge[1]]['position'].y]
                    z = [z_level, z_level]
                    ax.plot(x, y, zs=z, zdir='z', ls='-', color='grey',
                            alpha=0.2, linewidth=2)
            for edge in subgraph.edges():
                x = [self.uesgraph.node[edge[0]]['position'].x,
                     self.uesgraph.node[edge[1]]['position'].x]
                y = [self.uesgraph.node[edge[0]]['position'].y,
                     self.uesgraph.node[edge[1]]['position'].y]
                z = [z_level, z_level]
                ax.plot(x, y, zs=z, zdir='z', ls='-', color=network_color,
                        alpha=0.5, linewidth=2)

            for node in subgraph.nodes():
                x = self.uesgraph.node[node]['position'].x
                y = self.uesgraph.node[node]['position'].y
                z = z_level
                if 'is_supply_other' in self.uesgraph.node[node]:
                    if self.uesgraph.node[node]['is_supply_' + network_type]:
                        ax.scatter(x, y, zs=z, zdir='z',
                                   c=network_color, edgecolors=network_color,
                                   s=scaling_factor*2.5,
                                   alpha=0.8,
                                   depthshade=False)
                        ax.scatter(x, y, zs=z, zdir='z',
                                   c='green', edgecolors='green',
                                   s=scaling_factor*0.7,
                                   alpha=0.7,
                                   depthshade=False)
                        if dotted_lines is True:
                            x = [x, x]
                            y = [y, y]
                            z = [0, z_level]
                            ax.plot(x, y, zs=z, zdir='z', ls='dotted',
                                    color=network_color,
                                    alpha=0.7, linewidth=2)
                    else:
                        ax.scatter(x, y, zs=z, zdir='z',
                                   c='green', edgecolors='green',
                                   s=scaling_factor,
                                   alpha=0.7,
                                   depthshade=False)
                        if dotted_lines is True:
                            x = [x, x]
                            y = [y, y]
                            z = [0, z_level]
                            ax.plot(x, y, zs=z, zdir='z', ls='dotted',
                                    color='green',
                                    alpha=0.4, linewidth=2)
                else:
                    ax.scatter(x, y, zs=z, zdir='z',
                               c=network_color, edgecolors=network_color,
                               s=scaling_factor*0.5,
                               alpha=0.7,
                               depthshade=False)
        return ax

    def _add_node_marker(self, ax, nodelist, node_size=5, color='orange'):
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
            if self.uesgraph.node[building]['position'] is not None:
                ax.scatter(self.uesgraph.node[building]['position'].x,
                           self.uesgraph.node[building]['position'].y,
                           s=node_size,
                           color=color,
                           alpha=0.7)
        return ax

    def _add_edge_marker(self, ax, edge, color='orange'):
        """Adds a special edge marker

        Parameters
        ----------
        ax : matplotlib ax object
            Marker will be added to this ax object.
            `uesgraphVis.create_plot(ax)` should be run on this ax beforehand.
        edge : list
            A list of format [edge_0, edge_1]

        Returns
        -------
        ax : maplotlib ax object
        """
        nx.draw_networkx_edges(self.uesgraph,
                               pos=self.uesgraph.positions,
                               edgelist=[edge],
                               edge_color=color,
                               linewidths=None,
                               )
        return ax

    def _add_edge_data(self, ax, add_temperatures, add_flows, directions):
        """Plots temperatures and/ or mass flows on top of a network plot

        Parameters
        ----------
        ax : matplotlib ax handle
            Plot additions will be made to ax
        add_temperatures : boolean
            If True, adds temperature data by colormapping edge colors
        add_flows : boolean
            If True, varies line thickness according to edge flows
        directions : boolean
            Plots arrows for flow directions if True;
            If add_edge_flows is True, the arrows show the calculated flow
            direction.
        """
        scaling = 3
        if add_temperatures is True:
            temperatures = []
            for node in self.uesgraph.nodes():
                if 'temperature_supply' in self.uesgraph.node[node]:
                    temperatures.append(self.uesgraph.node[node][
                        'temperature_supply'])
            mean_temperature = np.mean(temperatures)
            std_temperatures = np.std(temperatures)
            temperature_min = max(min(temperatures),
                                  mean_temperature - 2 * std_temperatures)
            temperature_max = min(max(temperatures),
                                  mean_temperature + 2 * std_temperatures)

            print('temperature_min', temperature_min)
            print('temperature_max', temperature_max)

        if add_flows is True:
            mass_flows = []
            for edge in self.uesgraph.edges():
                mass_flows.append(self.uesgraph.edges[edge[0], edge[1]][
                                      'mass_flow'])
            mass_flow_max = max(mass_flows)

        for edge in self.uesgraph.edges():
            start = self.uesgraph.node[edge[0]]['position']
            end = self.uesgraph.node[edge[1]]['position']
            delta = start.distance(end)
            line = sg.LineString([start, end])

            T_added = False
            if add_temperatures is True:
                if 'temperature_supply' in self.uesgraph.node[
                        edge[0]] and 'temperature_supply' in \
                        self.uesgraph.node[edge[1]]:
                    if len(self.uesgraph.edges()) < 25:
                        discretization = 100
                    else:
                        discretization = 20
                    T1 = self.uesgraph.node[edge[0]]['temperature_supply']
                    T2 = self.uesgraph.node[edge[1]]['temperature_supply']
                    T_added = True
            if T_added is False:
                discretization = 2
                T1 = 367
                T2 = 367

            flow_added = False
            if add_flows is True:
                if 'mass_flow' in self.uesgraph.edges[edge[0], edge[1]]:
                    mass_flow = self.uesgraph.edges[edge[0], edge[1]][
                        'mass_flow']
                    linewidth = 1 + 4 * abs(mass_flow)/mass_flow_max
                    flow_added = True

            if flow_added is False:
                linewidth = 1

            t = np.linspace(0, 1, discretization)
            x = []
            y = []
            for i in t:
                here = line.interpolate(delta*i)
                x.append(float(here.x))
                y.append(float(here.y))

            t = np.linspace(T1, T2, discretization)

            points = np.array([x, y]).T.reshape(-1, 1, 2)

            segments = np.concatenate([points[:-1], points[1:]], axis=1)

            if add_temperatures is True:
                lc = LineCollection(segments, cmap=plt.get_cmap('viridis'),
                                    norm=plt.Normalize(temperature_min,
                                                       temperature_max))
                lc.set_array(t)
            else:
                colors = [matplotlib.colors.colorConverter.to_rgba('r')]
                print('colors', colors)
                lc = LineCollection(segments, colors=colors)

            lc.set_linewidth(linewidth*scaling)

            ax.add_collection(lc)

            if directions is True and add_flows is True:
                # Plot arrows for assumed flow direction
                for edge in self.uesgraph.edges():
                    mass_flow = self.uesgraph.edge[edge[0]][edge[1]][
                        'mass_flow']
                    if mass_flow > 0:
                        pos_0 = self.uesgraph.node[edge[0]]['position']
                        pos_1 = self.uesgraph.node[edge[1]]['position']
                    else:
                        pos_0 = self.uesgraph.node[edge[1]]['position']
                        pos_1 = self.uesgraph.node[edge[0]]['position']

                    # center = (pos_0 + pos_1) / 2
                    center = sg.LineString([pos_0, pos_1]).centroid
                    x = float(center.x)
                    y = float(center.y)
                    dx = (float(pos_1.x - pos_0.x)) / 4
                    dy = (float(pos_1.y - pos_0.y)) / 4

                    ax.arrow(x, y, dx, dy,
                             head_width=5, head_length=5, fc='k', ec='k')

        if 'problems' in self.uesgraph.graph:
            for node in self.uesgraph.graph['problems']:
                ax.scatter(self.uesgraph.node[node]['position'].x,
                           self.uesgraph.node[node]['position'].y,
                           s=40,
                           color='blue',
                           alpha=0.7)
                ax.text(self.uesgraph.node[node]['position'].x,
                        self.uesgraph.node[node]['position'].y,
                        s=str(node),
                        fontsize=4)
