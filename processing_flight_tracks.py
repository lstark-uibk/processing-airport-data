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

parentdir = "F:\\Uniarbeit 23_11_09\\data\\Data_airport\\Data_airport\\flights"
processed_dir = "F:\\Uniarbeit 23_11_09\\data\\Data_airport\\Data_airport\\flights\\processed_flights"
commentchar = "#"
plot_the_paths_for_checking = True

filenames_tracks = np.array(glob.glob(parentdir + "\\tracks\\*.csv", recursive=True))
filenames_flights_of_the_days = {}
filenames_flights_of_the_days["arrivals"] = np.array(glob.glob(parentdir + "\\*arrivals.csv", recursive=True))
filenames_flights_of_the_days["departures"] = np.array(glob.glob(parentdir + "\\*departures.csv", recursive=True))
date_pattern = re.compile(r'\d{4}-\d{2}-\d{2}')
dates_flights = {}

selected_dates = np.array(["2023-11-22"], dtype='datetime64[D]')
start_date = np.datetime64('2023-11-30')
end_date = np.datetime64('2023-12-08')
selected_dates = np.arange(start_date, end_date, dtype='datetime64[D]')
for arr_dep in ["arrivals","departures"]:
    dates_flights[arr_dep] = np.array([re.search(re.compile(r'\d{4}-\d{2}-\d{2}'), path).group() for path in filenames_flights_of_the_days[arr_dep]],dtype='datetime64[D]')
    dates_tracks = np.array([re.search(re.compile(r'(\d{4}-\d{2}-\d{2}T\d{2}_\d{2}_\d{2})'), path).group().replace('_', ':') for path in filenames_tracks], dtype = "datetime64[s]")

def read_in_data_of_one_day(date):
    print(f"Reading in data of the day: {date.astype('datetime64[D]').astype(str)}")

    tracks = {}
    flights = {}
    for arr_dep in ["arrivals","departures"]:
        filename_flights_of_the_date_selected = filenames_flights_of_the_days[arr_dep][dates_flights[arr_dep] == date.astype('datetime64[D]')]
        flights[arr_dep] = pd.DataFrame()
        try:
            df = pd.read_csv(filename_flights_of_the_date_selected[0], index_col=None, header=0)
            flights[arr_dep] = df
        except:
            print(f"Could not read in {filename_flights_of_the_date_selected}")
        flights[arr_dep]["near_overflight"] = np.nan
        flights[arr_dep]["overflight_time"] = np.nan
        flights[arr_dep]["overflight_from"] = np.nan
        flights[arr_dep]["minimal_distance"] = np.nan

        filenames_tracks_of_the_day_selected = filenames_tracks[dates_tracks.astype('datetime64[D]') == date.astype('datetime64[D]')]
        flight_names = [re.search(re.compile(r'([A-Z0-9-]+)\.csv'), path).group(1) for path in filenames_tracks_of_the_day_selected]
        for filename, flight in zip(filenames_tracks_of_the_day_selected,flight_names):
            print(filename,flight)
            try:
                df = pd.read_csv(filename, index_col=None, header=0, comment = '#',parse_dates=['timestamp'])
                index_repeat = df[(df == df.columns).all(axis=1)].index.min()      # get index of first iteration of the header
                if not pd.isna(index_repeat):
                    df = df[0:index_repeat]
                    df = df.apply(pd.to_numeric, errors='ignore')
                    df.timestamp = pd.to_datetime(df.timestamp)
                tracks[flight] = df
            except:
                pass
    return tracks, flights


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

def recalculate_latitudes(point,referencepoint_lon_lat):
    '''

    :param point: distance to refpoint x,  distance to refpoint x, height all in meters
    :param referencepoint_lon_lat:
    :return:
    '''
    #irgendwas läuft hier schief
    distx, disty ,height = point

    # Earth radius in meters
    earth_radius = 6371 * 1000  # Radius of the Earth in meters
    referencepoint_lat, referencepoint_lon, _ = referencepoint_lon_lat

    # because difference is small - math.cos(reference_lat
    lon_distance = distx/earth_radius/math.cos(math.radians(referencepoint_lat))
    lat_distance = disty/earth_radius

    lon_point = referencepoint_lon + math.degrees(lon_distance)
    lat_point = referencepoint_lat + math.degrees(lat_distance)
    return lat_point, lon_point, height

def gps_points_processing(latitude,longitude,altitude, times, arr_dep,flight_ident):
    """
    input the gps data and get information on the track
    :param latitude: np.array
    :param longitude: np.array
    :param altitude: np.array
    :param times: np.array UNIX time
    all input arrays have to be the same size
    :return: time_minimal_distance,minimal_distance_meters,point_minimal_distance
    time_minimal_distance: time when the plane is nearest in UNIX
    minimal_distance_meters: distance when the plane is nearest in meters
    point_minimal_distance: gps point where we are the neares
    """

    # print(f"Getting the processing ready with inputs {latitude},{longitude},{altitude},{times},{arr_dep}")
    fixed_point = np.array([47.262463, 11.369862, 580])
    distances_xy_meters = [calculate_xy_distances(fixed_point[:2],[lon,lat])for lon,lat in zip(latitude,longitude)]
    local_coords = np.c_[np.array(distances_xy_meters),altitude]
    timesref = times - times[0]
    # filter double times
    timesref, indices = np.unique(timesref, return_index=True)
    local_coords = local_coords[indices,:]



    tck, u = splprep(local_coords.T, u=timesref, s=0, k=1) # find spline representation of flight track


    # Define the fixed point outside the spline
    # Initial guess for parameter u
    if arr_dep == "arrivals":
        initial_guess = timesref[-1]
    if arr_dep == "departures":
        initial_guess = timesref[1]

    # Define a function that calculates the distance between the fixed point and the spline
    def distance_to_spline(u):
        point_on_spline = np.array(splev(u, tck))
        distance_to_point = np.linalg.norm(np.array([0, 0, 580]) - point_on_spline.T)
        return distance_to_point

    # Minimize the distance function to find the parameter u of the closest point
    time_minimal_distance_ref = minimize(distance_to_spline, initial_guess,  bounds = [(timesref[0],timesref[-1])]) #--> make the algrothm more exact
    time_minimal_distance = times[0] + time_minimal_distance_ref.x

    point_minimal_distance_meters_local = np.array(splev(time_minimal_distance_ref.x,tck)).T[0]
    minimal_distance_meters  = np.linalg.norm(point_minimal_distance_meters_local  - fixed_point)
    point_minimal_distance = recalculate_latitudes(point_minimal_distance_meters_local,fixed_point)
    dir_flight_at_minimal_distance = splev(time_minimal_distance_ref.x, tck, der=1)
    angle_radians = np.arctan2(dir_flight_at_minimal_distance[0], dir_flight_at_minimal_distance[1])
    angle_flight_at_minimal_distance_degrees = np.degrees(angle_radians)
    print(f"min dist {minimal_distance_meters} at {time_minimal_distance_ref.x} after flight start, this is {time_minimal_distance_ref.x - timesref[-1]} relative to the end")
    print(f"direction of {arr_dep} flight {dir_flight_at_minimal_distance}, with direction angle {angle_flight_at_minimal_distance_degrees}")
    overflight_ornot = 0
    if arr_dep == "arrivals":
        if -175 < angle_flight_at_minimal_distance_degrees < -5:
            overflight_ornot = 1
            #better checking of overflightornot
    if arr_dep == "departures":
        if 5 < angle_flight_at_minimal_distance_degrees < 175:
            overflight_ornot = 1
            #better checking of overflightornot
    print(f"overflight: {overflight_ornot}")
    print(local_coords.shape,timesref.shape)
    if plot_the_paths_for_checking:
        plt.scatter(local_coords[:,0],local_coords[:,1], s=20, c=timesref.astype(float), cmap = cm.jet)
        plt.scatter(point_minimal_distance_meters_local[0],point_minimal_distance_meters_local[1],marker='*')
        plt.scatter(47.262463, 11.369862, marker='*')
        landing_track_east_local = (-977.1572427143367, -85.6200935160446)
        landing_track_west_local = (-2931.6237985954726, -393.2964555414963)
        plt.plot([landing_track_east_local[0],landing_track_west_local[0]], [landing_track_east_local[1],landing_track_west_local[1]],linewidth = 10, color = "grey",zorder=1)
        arrowlength = 10
        plt.arrow(point_minimal_distance_meters_local[0],point_minimal_distance_meters_local[1], arrowlength*float(dir_flight_at_minimal_distance[0]), arrowlength*float(dir_flight_at_minimal_distance[1]), head_width=1000, head_length=1000, fc='red', ec='red')

        plt.gca().set_xlim(-10000, 10000)
        plt.gca().set_ylim(-10000, 10000)
        plt.gca().legend(["Flight path","Nearest Overflight", "Location Ursulinen","Landing track"])
        plt.title(f"flight {flight_ident}, {arr_dep}, overflight direction angle {angle_flight_at_minimal_distance_degrees}")
        plt.show()
        while plt.get_fignums():
            plt.pause(0.1)
    return time_minimal_distance,minimal_distance_meters,point_minimal_distance, overflight_ornot

### time minimal is way to early

for date in selected_dates:
    print(f"Processing the data of date {date.astype('datetime64[D]').astype(str)}")
    tracks, flights = read_in_data_of_one_day(date)
    for arr_dep in ["arrivals", "departures"]:
        for index,flight in flights[arr_dep].iterrows():
            print(index, date.astype('datetime64[D]').astype(str), flight.ident)
            flight_ident = flight.ident
            if flight_ident in tracks.keys():
                print("We have a track for this flight")
                track_this = tracks[flight_ident]
                times_UNIX = (track_this.timestamp.dt.tz_localize(None) - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
                # try:
                time_minimal_distance,minimal_distance_meters,point_minimal_distance, overflight_ornot = gps_points_processing(np.array(track_this.latitude), np.array(track_this.longitude), np.array(track_this.altitude), np.array(times_UNIX) , arr_dep, flight_ident)
                if overflight_ornot:
                    flights[arr_dep].loc[index, "near_overflight"] = overflight_ornot
                    flights[arr_dep].loc[index, "overflight_time"] = time_minimal_distance
                    if arr_dep == "arrivals":
                        flights[arr_dep].loc[index, "overflight_from"] = "W"
                    elif arr_dep == "departures":
                        flights[arr_dep].loc[index, "overflight_from"] = "E"
                    flights[arr_dep].loc[index, "minimal_distance"] = minimal_distance_meters
                # except Exception as error:
                #     print(f"------------------------------\nError in flight {flight_ident}: {error}")
            else:
                print("There is no track for this flight")
        savepath = os.path.join(processed_dir,f"{date.astype('datetime64[D]').astype(str)}_{arr_dep}_processed.csv")
        print(f"Saving the {arr_dep} of day {date.astype('datetime64[D]').astype(str)} to {savepath}")
        flights[arr_dep].to_csv(savepath)



