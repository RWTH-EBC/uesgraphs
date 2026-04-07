# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from pathlib import Path
from datetime import datetime

# use RWTH Colors
rwth_blue = "#00549F"
rwth_orange = "#F6A800"
rwth_red = "#CC071E"

# Matplotlib Style
try:
    plt.style.use("~\\ebc.paper.mplstyle")
except OSError:
    pass


def convert_dhw_load_to_storage_load(timeseries_df, start_plot, end_plot,
                                     dir_output, V_stor=300, dT_stor=55,
                                     dT_threshhold=10, Qcon_flow_max=5000,
                                     plot_cum_demand=False, with_losses=True,
                                     save_fig=True):
    """
    Converts the input DHW-Profile without a DHW-Storage to a DHW-Profile
    with a DHW-Storage. The output profile looks as if the HP would not
    supply the DHW-load directly but would rather re-heat the DHW-Storage,
    which has dropped below a certain dT Threshold. The advantage is, that no
    storage model has to be part of a dynamic simulation, although the
    heatpump still acts as if a storage is supplied. Based on DIN EN 12831-3.

    :param timeseries_df:   stores the DHW-demand profile in [W] per Timestep
    :param dir_output:      directory where figure is saved
    :param V_stor:          Storage Volume in Liters
    :param dT_stor:         max dT in Storage
    :param dT_threshhold:   max dT Drop before Storage needs to be re-heated
    :param Qcon_flow_max:   Heat Flow Rate at the Heatpump when refilling the
                            Storage in [W]
    :param plot_cum_demand: Plot the cumulative "Summenliniendiagram" as
                            described in DIN DIN EN 12831-3
    :param with_losses:     Boolean if the storage should have losses
    :param start_plot:      e.g. '2019-08-02'
    :param end_plot:        e.g. '2019-08-03'
    :param save_fig:        decide to save the fig as a pdf and png
    :return: storage_load:  DHW-profile that re-heats a storage.
    """

    # --- convert the DHW Demand ---
    s_step = int(timeseries_df.index.freqstr[:-1])
    timeseries_df['Heat_J'] = timeseries_df['Heat_W'] * s_step
    timeseries_df['Heat_kW'] = timeseries_df['Heat_W'] / 1000
    timeseries_df['Heat_kWh'] = timeseries_df['Heat_J'] / (3600 * 1000)

    # --- Storage Data ---
    # Todo: think about how Parameters should be for Schichtspeicher
    rho = 980 / 1000  # kg/L for Water (at 60°C? at 10°C its = 1)
    m_w = V_stor * rho  # Mass Water in Storage
    c_p = 4180  # Heat Capacity Water in [J/kgK]
    Q_full = m_w * c_p * dT_stor
    Q_full_kWh = Q_full / (3600 * 1000)
    dQ_threshhold = m_w * c_p * dT_threshhold
    Q_dh_timestep = Qcon_flow_max * s_step  # energy added in 1 timestep
    # Todo: implement a ramp-up period?

    # ---------- write storage load time series, with Losses --------
    Q_storr_curr = Q_full  # tracks the Storage Filling
    storage_load = []  # new time series
    storage_level = []
    loss_load = []
    fill_storage = False

    for t_step, dem_step in enumerate(timeseries_df['Heat_J'], start=0):
        storage_level.append(Q_storr_curr)
        if with_losses:
            Q_loss = (Q_storr_curr * 0.001 * s_step) / 3600  # 0,1% Loss/Hour
        else:
            Q_loss = 0
        loss_load.append(Q_loss)

        # for initial condition, when storage_load is still empty
        if len(storage_load) == 0:
            Q_storr_curr = Q_storr_curr - dem_step - Q_loss
        else:
            Q_storr_curr = Q_storr_curr - dem_step - Q_loss \
                           + storage_load[t_step - 1]

        if Q_storr_curr >= Q_full:  # storage full, dont fill it!
            fill_storage = False
            storage_load.append(0)
            continue

        # storage above dT Threshhold, but not full.
        # depending if is charging or discharging, storage_load is appended
        elif Q_storr_curr > Q_full - dQ_threshhold:
            if fill_storage:
                storage_load.append(Q_dh_timestep)
            else:
                storage_load.append(0)
                continue

        else:  # storage below dT Threshhold, fill it!
            fill_storage = True
            storage_load.append(Q_dh_timestep)

    # append new Storage lists to Dataframe
    timeseries_df['StorageLoad_J'] = storage_load
    timeseries_df['StorageLoad_kW'] = timeseries_df['StorageLoad_J'] / (
            s_step * 1000)
    timeseries_df['StorageLoad_kWh'] = timeseries_df['StorageLoad_J'] / (3600
                                                                         * 1000)
    timeseries_df['StorageLosses_J'] = loss_load
    timeseries_df['StorageLosses_W'] = timeseries_df['StorageLosses_J'] / s_step
    timeseries_df['StorageLosses_kWh'] = timeseries_df['StorageLosses_J'] / (
            3600 * 1000)

    # print out total demands and Difference between them
    print("Sum DHW Demand = {:.2f} kWh".format(sum(timeseries_df['Heat_kWh'])))
    print("Sum Storage Demand = {:.2f} kWh".format(sum(timeseries_df[
                                                           'StorageLoad_kWh'])))
    print("Sum Storage Losses = {:.2f} kWh".format(sum(timeseries_df[
                                                           'StorageLosses_kWh'])))

    diff = timeseries_df['Heat_kWh'].sum() + timeseries_df[
        'StorageLosses_kWh'].sum() - timeseries_df['StorageLoad_kWh'].sum()
    print("DHW + Losses - StorageLoad = {:.2f} "
          "kWh".format(diff))

    if diff < 0:
        print("More heat than dhw demand is added to the storage in"
              "loss-less mode!")

    # cumulative demand (german: "Summenlinien")
    dhw_demand_sumline = []
    acc_dem = 0  # accumulated demand
    for dem_step in timeseries_df['Heat_kWh']:
        acc_dem += dem_step
        dhw_demand_sumline.append(acc_dem)
    timeseries_df['Heat_Sumline_kWh'] = dhw_demand_sumline

    storage_load_sumline = []
    acc_load = 0  # accumulated load
    for i, stor_step in enumerate(timeseries_df['StorageLoad_kWh']):
        acc_load += stor_step - timeseries_df['StorageLosses_kWh'][i]
        storage_load_sumline.append(acc_load)
    storage_load_sumline = [Q + Q_full_kWh for Q in storage_load_sumline]
    timeseries_df['StorageLoad_Sumline_kWh'] = storage_load_sumline

    # Todo: Fill storage so that at the end of the year its full again
    fill_storage = False
    if fill_storage:
        last_zero_index = None
        for idx, item in enumerate(reversed(storage_load), start=0):
            if item == 0:
                last_zero_index = idx
        storage_load[last_zero_index] += diff

    # Plot the cumulative demand
    if plot_cum_demand:

        sns.set_style("white")
        sns.set_context("paper")

        # decide how to resample data based on plot interval
        timedelta = pd.Timedelta(pd.Timestamp(end_plot) - pd.Timestamp(
            start_plot))

        if timedelta.days < 3:
            resample_delta = "600S"  # 10min
        elif timedelta.days < 14:  # 2 Weeks
            resample_delta = "1800S"  # 30min
        elif timedelta.days < 62:  # 2 months
            resample_delta = "H"  # hourly
        else:
            resample_delta = "D"

        # make figures with 3 different y-axes
        fig, ax1 = plt.subplots()
        fig.tight_layout()

        ax1_data = timeseries_df[['Heat_Sumline_kWh',
                                  'StorageLoad_Sumline_kWh']][
                   start_plot:end_plot]
        ax1 = sns.lineplot(data=ax1_data.resample(resample_delta).mean(),
                           dashes=[(6, 2), (6, 2)], linewidth=1.2,
                           palette=[rwth_blue, rwth_orange])

        ymin1, ymax1 = ax1.get_ylim()
        ax1.set_ylim(ymin1, ymax1 * 1.01)

        ax2 = ax1.twinx()
        ax2_data = timeseries_df[['Heat_kW', 'StorageLoad_kW']][
                   start_plot:end_plot]
        sns.lineplot(ax=ax2, data=ax2_data.resample(resample_delta).mean(),
                     dashes=False, linewidth=1,
                     palette=[rwth_blue, rwth_orange])

        ymin2, ymax2 = ax2.get_ylim()
        ax2.set_ylim(ymin2, ymax2 * 1.03)

        ax3 = ax1.twinx()
        ax3_data = timeseries_df[['StorageLosses_W']][start_plot:end_plot]
        sns.lineplot(ax=ax3, data=ax3_data.resample(resample_delta).mean(),
                     dashes=False, linewidth=0.7, palette=[rwth_red])

        ymin3, ymax3 = ax3.get_ylim()
        ax3.set_ylim(ymin3, ymax3 * 1.1)

        ax3.spines["right"].set_position(("axes", 1.12))

        # make one legend for the figure
        ax1.legend_.remove()
        ax2.legend_.remove()
        ax3.legend_.remove()
        fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9), frameon=True,
                   prop={'size': 8}
                   )

        ax1.set_ylabel('cumulative Demand and Supply [kWh]')
        ax2.set_ylabel('current Demand and Supply [kW]')
        ax3.set_ylabel('Losses [W]')
        ax1.grid(False)
        ax2.grid(False)
        ax3.grid(False)

        # set the x axis ticks
        # https://matplotlib.org/3.1.1/gallery/ticks_and_spines/date_concise_formatter.html
        locator = mdates.AutoDateLocator()
        formatter = mdates.ConciseDateFormatter(locator)
        ax1.xaxis.set_major_locator(locator)
        ax1.xaxis.set_major_formatter(formatter)

        # Count number of clusters of non-zero values ("peaks").
        # One Peak is comprised by 2 HP mode switches.
        dhw_peaks = int(np.diff(np.concatenate(
            [[0], list(timeseries_df['Heat_J']), [0]]) == 0).sum() / 2)
        stor_peaks = int(np.diff(np.concatenate(
            [[0], list(timeseries_df['StorageLoad_J']), [0]]) == 0).sum() / 2)

        method = timeseries_df['method'][0]

        plt.title('{} Demand ({} Peaks, {} per Day) and Storage ({} Peaks, '
                  '{} per Day)'.format(method, dhw_peaks, round(dhw_peaks /
                                                               365, 2),
                                       stor_peaks, round(stor_peaks / 365, 2)))
        plt.show()

        if save_fig:
            save_name = 'Storage_Load_' + str(datetime.now().strftime(
                '%Y_%m_%d_%H_%M_%S')) + '.pdf'
            fig.savefig(dir_output / save_name)

    return timeseries_df
