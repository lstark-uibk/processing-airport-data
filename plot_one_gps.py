import datetime
import numpy as np
import math
import glob
import os
from pathlib import Path
import pandas as pd
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib  import cm
import matplotlib.dates as mdates
from scipy.interpolate import splprep, splev
from scipy.spatial import distance
from scipy.optimize import minimize
import re
import pytz
import params
import readinflights

def calculate_xy_distances(point1, point2):
    """
    Calculate the x and y distances (in meters) between two points specified
    by latitude and longitude.

    Parameters:
    lat1, lon1: Latitude and longitude of the first point (in degrees)
    lat2, lon2: Latitude and longitude of the second point (in degrees)

    Returns:
    A tuple (x_distance, y_distance) in meters.
    """
    # Calculate the great-circle distance in kilometers
    lat1, lon1 = point1
    lat2, lon2 = point2
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Earth radius in meters
    earth_radius = 6371 * 1000  # Radius of the Earth in meters

    # Calculate the x and y distances in meters
    x_distance = (lon2 - lon1) * earth_radius * math.cos(0.5 * (lat1 + lat2))   #(lon2 - lon1) * earth_radius would be the distance at equator  math.cos(0.5 * (lat1 + lat2)) is the scaling down to a vertical circle at latitude in the middle of the two
    y_distance = (lat2 - lat1) * earth_radius

    return x_distance, y_distance

parentdir = params.parentdir
dates = params.selected_dates
tracksdir = parentdir + f"\\flights\\tracks\\*.csv"

filenames_tracks = np.array(glob.glob(params.parentdir + "\\flights\\tracks\\*", recursive=True))
flights = pd.DataFrame([])
# old_data = {"arrivals": np.array([]), "departures": np.array([])}
for date in dates:
    for arr_dep in ["arrivals", "departures"]:
        files_raw = parentdir + f"\\flights\\*{arr_dep}*.csv"
        filenames_flights_raw = np.array(glob.glob(files_raw, recursive=True))
        filenames_flights_raw = np.array([x for x in filenames_flights_raw if ('sched' not in x) and ('fr24' not in x)])
        filenames_flights_raw, last_version_raw = params.get_file_date_and_last_version(filenames_flights_raw, [date])
        try:
            print("Try raw flight data .")
            flights_arr_dep = readinflights.read_in_data_of_one_file(filenames_flights_raw, processed=False)
            flights_arr_dep["arr_dep"] = arr_dep
            flights = pd.concat([flights, flights_arr_dep])
        except:
            print("Could not load flight data")

tracksfp = np.array(glob.glob(tracksdir, recursive=True))
tracks = readinflights.read_in_tracks_of_multiples_days(tracksfp, dates)

fig, axis_gps = plt.subplots(1)
fig2, axis_gps_zoomed = plt.subplots(1)
plt.show(block = False)
i = 0
while True:

    furtherprocessing_possible = True

    flight_name = input("What flight you want to process (either ident or index, exit to stop program)?")
    axis_gps.clear()
    axis_gps_zoomed.clear()
    try:
        data_this = tracks[flight_name]
    except:
        try:
            flight_name = list(tracks.keys())[int(flight_name)]
            data_this = tracks[flight_name]
        except:
            furtherprocessing_possible = False
    if furtherprocessing_possible:
        flightinfo = flights[flights.ident == flight_name]
        print(f"({i+1}/{len(tracks)}){flightinfo.ident}, actual_on_off: {flights[flights.ident == flight_name].index}")

        landing_track_east_local = (-977.1572427143367, -85.6200935160446)
        landing_track_west_local = (-2931.6237985954726, -393.2964555414963)
        axis_gps.plot([landing_track_east_local[0], landing_track_west_local[0]],
                      [landing_track_east_local[1], landing_track_west_local[1]], linewidth=10, color="grey", zorder=1)
        axis_gps_zoomed.plot([landing_track_east_local[0], landing_track_west_local[0]],
                      [landing_track_east_local[1], landing_track_west_local[1]], linewidth=10, color="grey", zorder=1)


        fixed_point = np.array([47.262463, 11.369862, 580])
        distances_xy_meters = [calculate_xy_distances(fixed_point[:2],[lat,lon])for lat,lon in zip(data_this.latitude,data_this.longitude)]
        local_coords = np.c_[np.array(distances_xy_meters),data_this.altitude_m]
        timesref = data_this.timestamp - data_this.timestamp[0]
        # filter double times
        timesref, indices = np.unique(timesref, return_index=True)
        local_coords = local_coords[indices,:]
        for index in np.round(np.linspace(0, local_coords[:, 0].size - 1, 8)).astype(int):
            axis_gps.text(local_coords[index, 0], local_coords[index, 1],
                          datetime.datetime.strftime(data_this.timestamp[index], "%H:%M"),
                          rotation=45)
        axis_gps.scatter(local_coords[:, 0], local_coords[:, 1], s=20, c=timesref.astype(float), cmap=cm.jet)
        axis_gps.scatter(47.262463, 11.369862, marker='*')
        axis_gps_zoomed.scatter(local_coords[:, 0], local_coords[:, 1], s=20, c=timesref.astype(float), cmap=cm.jet)
        axis_gps_zoomed.scatter(47.262463, 11.369862, marker='*')
        axis_gps_zoomed.set_xlim(-15000, 15000)
        axis_gps_zoomed.set_ylim(-15000, 15000)

        fig.suptitle(
            f"{flightinfo.ident.iloc[0]}, {flightinfo.arr_dep.iloc[0]}, actual_on/off: {flightinfo['actual_on'].iloc[0].strftime('%Y-%m-%d %H:%M')}/{flightinfo['actual_off'].iloc[0].strftime('%Y-%m-%d %H:%M')}")
        fig2.suptitle(
            f"{flightinfo.ident.iloc[0]}, {flightinfo.arr_dep.iloc[0]}, actual_on_off:  {flightinfo['actual_on'].iloc[0].strftime('%Y-%m-%d %H:%M')}/{flightinfo['actual_off'].iloc[0].strftime('%Y-%m-%d %H:%M')}")

        plt.pause(0.2)
    else:
        print("There was no gps data for this flight")

    if flight_name == "exit":
        break