"""
This module includes TEASER for the demand estimation based on the .geojson
"""

import os
import json
import pandas as pd
import subprocess
import simulate as sim
import datetime
import multiprocessing
from pathlib import Path
import shutil

import logging
import tempfile

from teaser.project import Project
from dymola.dymola_interface import DymolaInterface

def set_up_logger(name,log_dir = None,level=int(logging.ERROR)):
    """Sets up a configured logger with file handler.
    
    Creates a logger with specified name and logging level.
    Log files are stored in a directory with timestamp in filename.
    If no directory is specified, the system's temporary directory is used.
    
    Args:
        name (str): Name of the logger, also used for filename
        log_dir (str, optional): Directory for log files.
            Defaults to None (uses temp directory)
        level (int, optional): Logging level (e.g. logging.ERROR, logging.INFO).
            Defaults to logging.ERROR
    
    Returns:
        logging.Logger: Configured logger object
        
    Example:
        >>> logger = set_up_logger("my_app", "/var/log", logging.INFO)
        >>> logger.info("Application started")
        
    Notes:
        - Log filename format: {name}_{YYYYMMDD_HHMMSS}.log
        - Log entry format: time - logger_name - [file:line] - level - message
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if log_dir == None:
        log_dir = tempfile.gettempdir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"{name}_{timestamp}.log")
    print(f"Logfile findable here: {log_file}")
    handler = logging.FileHandler(log_file)
    formatter = logging.Formatter('%(asctime)s - %(name)s - [%(filename)s:%(lineno)d] - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

def create_project():
    """Create a TEASER project for current version."""
    prj = Project()
    # Set default calculation parameters
    prj._number_of_elements_calc = 2  # AixLib requires 2 elements
    prj._merge_windows_calc = False   # Default for AixLib ebc calculation
    prj._used_library_calc = "AixLib"
    prj.name = "Demand_Estimation"
    return prj

def create_district(info_path, prj, logger=None):
    """Create TEASER buildings using modern API, according to infos in geojson.

    Parameters
    ----------
    info_path : path
        Full path to json with building infos.
    district_name : string
        Name of district
    prj : TEASER project
        Project class where buildings should be added to.
    """
    district_file = info_path
    
    if not os.path.exists(district_file):
        raise FileNotFoundError(f"District file not found: {district_file}")
    
    with open(district_file) as json_file:
        geojson = json.load(json_file)

    building_info = geojson.get("features", [])

    logger.info(f"Processing {len(building_info)} buildings...")
    
    successful_buildings = 0
    for i in range(0,len(building_info)):
        try:
            bldg_info = building_info[i]["properties"]
            if i % 5 == 0 or i <= 10:  # More frequent feedback
                logger.info(f"  Processing building {i}/{len(building_info)}: {bldg_info['name']}")
                
            # Map archetype to TEASER geometry_data
            archetype = bldg_info["archetype"]
            building = None  # Initialize building variable
            
            if archetype in ["OfficeExisting", "OfficeWithDataCenter", "OfficeHighRise", "OfficeHighRiseKita"]:
                # Use modern TEASER API for non-residential buildings
                building = prj.add_non_residential(
                    construction_data='iwu_heavy',
                    geometry_data='bmvbs_office',
                    name=bldg_info["name"],
                    year_of_construction=bldg_info["year_of_construction"],
                    number_of_floors=bldg_info["number_of_floors"],
                    height_of_floors=bldg_info["height_of_floors"],
                    net_leased_area=bldg_info["net_leased_area"],
                    with_ahu=bldg_info["with_ahu"],
                    internal_gains_mode=bldg_info["internal_gains_mode"]
                )
            elif archetype in ["MultiFamilyHouse"]:
                # Use modern TEASER API for multi-family residential buildings
                building = prj.add_residential(
                    construction_data='tabula_de_standard',
                    geometry_data='tabula_de_multi_family_house',
                    name=bldg_info["name"],
                    year_of_construction=bldg_info["year_of_construction"],
                    number_of_floors=bldg_info["number_of_floors"],
                    height_of_floors=bldg_info["height_of_floors"],
                    net_leased_area=bldg_info["net_leased_area"],
                    with_ahu=bldg_info["with_ahu"],
                    internal_gains_mode=bldg_info["internal_gains_mode"]
                )
            elif archetype in ["SingleFamilyHouse"]:
                # Use modern TEASER API for single-family residential buildings
                building = prj.add_residential(
                    construction_data='tabula_de_standard',
                    geometry_data='tabula_de_single_family_house',
                    name=bldg_info["name"],
                    year_of_construction=bldg_info["year_of_construction"],
                    number_of_floors=bldg_info["number_of_floors"],
                    height_of_floors=bldg_info["height_of_floors"],
                    net_leased_area=bldg_info["net_leased_area"],
                    with_ahu=bldg_info["with_ahu"],
                    internal_gains_mode=bldg_info["internal_gains_mode"]
                )
            else:
                logger.info(f"⚠️  Warning: Unknown archetype '{archetype}' for building '{bldg_info['name']}' - skipping")
                continue
                
            successful_buildings += 1
            
            # Apply any additional customizations to the created building if needed
            # (The modern TEASER API already handles most parameter calculations)
            # if building is not None:
            #     # Apply load corrections if needed
            #     for zone in building.thermal_zones:
            #         if hasattr(zone, 'model_attr') and hasattr(zone.model_attr, 'heat_load'):
            #             zone.model_attr.heat_load = zone.model_attr.heat_load * 1.012
            #             if zone.model_attr.heat_load / zone.area > 26.0:
            #                 zone.model_attr.heat_load = zone.area * 26.0
            #             if zone.model_attr.heat_load / zone.area < 24.5:
            #                 zone.model_attr.heat_load = zone.area * 24.5
            #             if "ICT" in zone.name:
            #                 if hasattr(zone.model_attr, 'cool_load'):
            #                     zone.model_attr.cool_load = zone.model_attr.cool_load * 4
                    
        except Exception as e:
            logger.info(f"⚠️  Warning: Could not process building '{i}': {e}")
            continue
    
    logger.info(f"Successfully created {successful_buildings}/{len(building_info)} buildings")
    
    # Ensure all buildings have their parameters calculated for export
    logger.info("Calculating building parameters for export...")
    prj.calc_all_buildings()
    
    return prj

def read_results(
    prj,
    buildings,
    signals,
    index,
    stop_time,
    timestep,
    results_path=None,
    csv_path=None,
    indoor_air=False,
    logger=None
):
    """Read simulation data from .mat file and save them into csv.

    Reads Dymola result files and saves them as time series in csv. Naming
    convention of time series follows proposed naming schema of Team GA. It
    assumes that all thermal_zones in PostgreSQL database are modeled as a
    thermal zone in Modelica. Thus this approach is not yet ready to be used
    with archetypes.

    Parameters
    ----------
    prj : TEASER Project() instance
        TEASER Project with all buildings that have been simulated. Names need
        to be identical.
    buidlings : list
        List of buildings whose results should be read.
    signals : list
            List of signals to be read from the results file.
    index : Pandas date_range
        Pandas date range of the simulation data. Must fit the length of
        simulation data. (default: hourly for year 2015)
    results_path : str
        Path where Dymola results are  stored.
    csv_path : str
        Path where csv results should be stored.
    indoor_air : boolean
        If true, output csv-file contains dataframe with one column for each given
        signal. If false, Heater and Cooler signals are expected and seperate output
        csv-files are created for both signals.
    """

    if not os.path.exists(csv_path):
        os.makedirs(csv_path)
    dymola = DymolaInterface()

    for bldg in buildings:
        logger.info("reading building {}".format(bldg.name))

        pd.DataFrame
        if not (bldg.name + "_heat.csv") in os.listdir(csv_path):
            try:
                logger.info(os.path.join(results_path, bldg.name + ".mat"))

                dym_res = dymola.readTrajectory(
                    fileName=os.path.join(results_path, bldg.name + ".mat"),
                    signals=signals,
                    rows=dymola.readTrajectorySize(
                        fileName=os.path.join(results_path, bldg.name + ".mat")
                    ),
                )
                results = pd.DataFrame().from_records(dym_res).T
                results = results.rename(
                    columns=dict(zip(results.columns.values, signals))
                )
            except BaseException:
                # Dymola has strange exceptions
                logger.info(
                    "Reading results of building {} failed, "
                    "please check result file".format(bldg.name)
                )
                raise Exception("Results Error!")
                continue
            try:
                results = results.iloc[1:]
                results.index = index
            except ValueError:
                logger.info(
                    "Simulation results of building {} are most likely "
                    "faulty (series is shorter then one year), please check "
                    "result file".format(bldg.name)
                )
                raise Exception("Completion Error!")

            if indoor_air is False:
                heat = pd.DataFrame(
                    data=results.filter(like="PHeat").sum(axis=1),
                    index=results.index,
                    columns=[bldg.name],
                )

                cool = pd.DataFrame(
                    data=results.filter(like="PCool").abs().sum(axis=1),
                    index=results.index,
                    columns=[bldg.name],
                )

                heat.to_csv(os.path.join(csv_path, bldg.name + "_heat.csv"))
                cool.to_csv(os.path.join(csv_path, bldg.name + "_cool.csv"))

                heat.index = [(i) * timestep for i in range(int(stop_time/timestep))]
                heat.to_csv(
                    os.path.join(csv_path, bldg.name + "_heat.txt"), header=False)

                cool.index = [(i) * timestep for i in range(int(stop_time/timestep))]
                cool.to_csv(os.path.join(
                    csv_path, bldg.name + "_cool.txt"), header=False)

            else:
                results.to_csv(os.path.join(csv_path, bldg.name + "_indoor_air.csv"))

    dymola.close()

def run_simulation(buildings_info_path, weather_path=None, timestep=3600, stop_time=8760*3600 , logger=None):
    DIR_SCRIPT = os.path.abspath(os.path.dirname(__file__))
    DIR_TOP = os.path.abspath(DIR_SCRIPT)

    timesteps = int(stop_time / timestep)

    index = pd.date_range(datetime.datetime(2025, 1, 1), periods=timesteps, freq="1h")

    # Check if weather files exist
    if weather_path is None or not os.path.exists(weather_path):
        logger.info(f"Warning: Weather file not found or given at {weather_path}, using default weather file.")
        weather_path = os.path.join(DIR_SCRIPT, "weather-seestadt-ref-2015.mos")

    # === Reference Scenario ===
    prj = create_project()
    prj.weather_file_path = weather_path

    logger.info("Creating district buildings...")
    prj = create_district(
        info_path=buildings_info_path, prj=prj, logger=logger
    )
    logger.info(f"Created {len(prj.buildings)} buildings")

    RESULTS_PATH = os.path.join(DIR_TOP, "tmp_TEASER_results")
    if not os.path.exists(RESULTS_PATH):
        os.makedirs(RESULTS_PATH)

    logger.info("Exporting AixLib models...")
    export_path = prj.export_aixlib()  # This returns the export path
    prj.save_project()

    logger.info(f"Models exported to: {export_path}")

    Aix_Path = Path(DIR_SCRIPT)

    Aix_Path.mkdir(exist_ok=True)
    aixlib_dir = Aix_Path.joinpath("AixLib")
    if not aixlib_dir.exists():
        logger.info(f"Cloning AixLib repository to {aixlib_dir}...")
        subprocess.run(
            ["git", "clone", "https://github.com/RWTH-EBC/AixLib", str(aixlib_dir)],
            check=True
        )
    path_aixlib = aixlib_dir.joinpath("AixLib/package.mo")
    logger.info(f"Using AixLib from: {path_aixlib}")


    demand_csv_path = os.path.join(DIR_SCRIPT, "demands_TEASER")
    if not os.path.exists(demand_csv_path):
        os.makedirs(demand_csv_path)

    logger.info("Starting simulations...")
    sim.queue_simulation(
        sim_function=sim.simulate,
        prj=prj,
        results_path=RESULTS_PATH,
        stop_time=stop_time,
        output_interval=timestep,
        number_of_workers=max(1, multiprocessing.cpu_count() - 4),
        aixlib_path=str(path_aixlib.parent),
    )
    for bldg in prj.buildings:
        signals = [
            "multizone.PHeater[{}]".format(i + 1)
            for i in range(len(bldg.thermal_zones))
        ]
        signals += [
            "multizone.PCooler[{}]".format(i + 1)
            for i in range(len(bldg.thermal_zones))
        ]
        read_results(
            prj=prj,
            signals=signals,
            buildings=[bldg],
            index=index,
            results_path=os.path.join(RESULTS_PATH, prj.name),
            csv_path=os.path.join(RESULTS_PATH, prj.name, "demand_csv"),
            stop_time=stop_time,
            timestep=timestep,
            logger=logger
        )
    
    heat = pd.DataFrame(index=index)
    cool = pd.DataFrame(index=index)
    heat_list = []
    cool_list = []
    for bldg in prj.buildings:
        bldg_heat_df = pd.read_csv(os.path.join(RESULTS_PATH, prj.name, "demand_csv", bldg.name + "_heat.csv"), index_col=0, parse_dates=True)
        bldg_cool_df = pd.read_csv(os.path.join(RESULTS_PATH, prj.name, "demand_csv", bldg.name + "_cool.csv"), index_col=0, parse_dates=True)
        heat_list.append(bldg_heat_df)
        cool_list.append(bldg_cool_df)

    heat = pd.concat(heat_list, axis=1)
    cool = pd.concat(cool_list, axis=1)

    heat.to_csv(os.path.join(demand_csv_path, "demands-heat.csv"))
    cool.to_csv(os.path.join(demand_csv_path, "demands-cool.csv"))
    
    shutil.rmtree(RESULTS_PATH)

if __name__ == "__main__":
    uesgraphs_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(uesgraphs_dir, 'uesgraphs', 'data', 'examples')
    geojson_dir = os.path.join(data_dir, 'e15_geojson')

    buildings_geojson = os.path.join(geojson_dir, 'buildings_teaser_info.geojson')

    logger= set_up_logger("teaser_integration", level=logging.INFO)

    run_simulation(buildings_geojson, logger=logger)