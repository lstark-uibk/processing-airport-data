# with this script you can automatically read in the flight tracks and find out the minimum distance,
# the time at which the airplane is nearest and the direction the overflight come from

# first change the parentdir and date you want to process in the params file

# The program will check all tracks in params.flightsprocessed_dir and then get the information out of the track
# Sometimes the track is unclear. Then it will plot a graph for a visual check which you will have to fill out
# then all the info is saved in parentdir+"flights\\processed_flights\\Flightinfo_processed"
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
import readinpartector
import readinmicrophone
import readinweather


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
def gps_points_processing(latitude,longitude,altitude, times,refpoint, arr_dep,flight_ident,threshforvischeck, axis_gps, plot_all):
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
    fixed_point = np.array(refpoint)
    distances_xy_meters = [calculate_xy_distances(fixed_point[:2],[lat,lon])for lat,lon in zip(latitude,longitude)]
    local_coords = np.c_[np.array(distances_xy_meters),altitude]
    timesref = times - times[0]
    # filter double times
    timesref, indices = np.unique(timesref, return_index=True)
    local_coords = local_coords[indices,:]
    usable = 1
    change_arrdep_to = 0
    changed_overflighttime = 0


    tck, u = splprep(local_coords.T, u=timesref, s=0, k=1) # find spline representation of flight track


    # Define the fixed point outside the spline
    # Initial guess for parameter u
    if arr_dep == "arrivals":
        initial_guess = timesref[-1]
        group = 1
    if arr_dep == "departures":
        initial_guess = timesref[1]
        group = 2

    # Define a function that calculates the distance between the fixed point and the spline
    def distance_to_spline(u):
        point_on_spline = np.array(splev(u, tck))
        distance_to_point = np.linalg.norm(np.array([0, 0, 580]) - point_on_spline.T)
        return distance_to_point

    # Minimize the distance function to find the parameter u of the closest point
    time_minimal_distance_ref = minimize(distance_to_spline, initial_guess,  bounds = [(timesref[0],timesref[-1])]) #--> make the algrothm more exact
    time_minimal_distance = times[0] + time_minimal_distance_ref.x
    time_minimal_distance = time_minimal_distance[0]

    point_minimal_distance_meters_local = np.array(splev(time_minimal_distance_ref.x,tck)).T[0]
    minimal_distance_meters  = np.linalg.norm(point_minimal_distance_meters_local  - fixed_point)
    point_minimal_distance = recalculate_latitudes(point_minimal_distance_meters_local,fixed_point)
    dir_flight_at_minimal_distance = splev(time_minimal_distance_ref.x, tck, der=1)
    angle_radians = np.arctan2(dir_flight_at_minimal_distance[0], dir_flight_at_minimal_distance[1])
    angle_flight_at_minimal_distance_degrees = np.degrees(angle_radians)

    overflight_ornot = 0
    text_overflight = "NO OVERFLIGHT"
    plot_the_paths_for_checking = plot_all
    if arr_dep == "arrivals":
        if -175 < angle_flight_at_minimal_distance_degrees < -5:
            overflight_ornot = 1
            text_overflight = "OVERFLIGHT"
            print(f"This is an overflight")
            #better checking of overflightornot
            if np.linalg.norm((point_minimal_distance_meters_local - fixed_point)[0:2]) > 200:
                print(f"There is something wrong in the minimal distance -> make visual check")
                plot_the_paths_for_checking = True
    if arr_dep == "departures":
        if 5 < angle_flight_at_minimal_distance_degrees < 175:
            overflight_ornot = 1

            text_overflight = "OVERFLIGHT"
            print(f"This is an overflight")
            #better checking of overflightornot
            if np.linalg.norm((point_minimal_distance_meters_local - fixed_point)[0:2]) > threshforvischeck:
                print(f"There is something wrong in the minimal distance -> make visual check")
                plot_the_paths_for_checking = True
    print(f"This is an {text_overflight}")
    if overflight_ornot:
        group_this = group
    else:
        group_this = group+2
    if plot_the_paths_for_checking:
        landing_track_east_local = (-977.1572427143367, -85.6200935160446)
        landing_track_west_local = (-2931.6237985954726, -393.2964555414963)
        axis_gps.plot([landing_track_east_local[0],landing_track_west_local[0]], [landing_track_east_local[1],landing_track_west_local[1]],linewidth = 10, color = "grey",zorder=1)
        arrowlength = 10
        axis_gps.arrow(point_minimal_distance_meters_local[0],point_minimal_distance_meters_local[1], arrowlength*float(dir_flight_at_minimal_distance[0][0]), arrowlength*float(dir_flight_at_minimal_distance[1][0]), head_width=1000, head_length=1000, fc='red', ec='red', label='_nolegend_')
        axis_gps.scatter(local_coords[:,0],local_coords[:,1], s=20, c=timesref.astype(float), cmap = cm.jet)
        axis_gps.scatter(point_minimal_distance_meters_local[0],point_minimal_distance_meters_local[1],marker='*')
        axis_gps.scatter(47.262463, 11.369862, marker='*')

        for index in np.round(np.linspace(0, local_coords[:,0].size - 1, 8)).astype(int):
            axis_gps.text(local_coords[index,0], local_coords[index,1],
                       datetime.datetime.strftime(datetime.datetime.fromtimestamp(times[index], tz=pytz.UTC),"%H:%M"), rotation=45)
        direction_vector = np.array(dir_flight_at_minimal_distance)[:,0]
        if arr_dep == "arrivals":
            timestep = 10
            index_local_coords = -1
        else:
            timestep = -10
            index_local_coords = 0
        furtherinterpol = np.array([x * direction_vector  for x in [timestep * y for y in range(1, 100)]])
        furtherinterpol_ref = furtherinterpol+ local_coords[index_local_coords, :]
        axis_gps.scatter(furtherinterpol_ref[:,0],furtherinterpol_ref[:,1],c="k")
        for i, seconds_after_last_point in enumerate([timestep*x for x in range(1,100)]):
            axis_gps.text(furtherinterpol_ref[i,0],furtherinterpol_ref[i,1],f"{seconds_after_last_point}s",rotation=45)


    ############## show the times
        axis_gps.set_xlim(-5000, 5000)
        axis_gps.set_ylim(-5000, 5000)
        axis_gps.legend(["Landing track","Flight path","Nearest Overflight", "Location Ursulinen",])
        plt.title(f"{text_overflight}  flight {flight_ident}, {arr_dep}, group {group_this}, distance {round(minimal_distance_meters)}m,angle {round(angle_flight_at_minimal_distance_degrees[0])}deg ")
        print(f"overflight: {overflight_ornot}")
        print(f"min dist {minimal_distance_meters} at {datetime.datetime.strftime(datetime.datetime.fromtimestamp(int(round(time_minimal_distance)), tz=pytz.UTC),'%H:%M:%S')} ")
        print(f"direction of {arr_dep} flight {dir_flight_at_minimal_distance}, with direction angle {angle_flight_at_minimal_distance_degrees}")
        plt.show(block = False)
        plt.pause(0.1)
        restart_loop = True
        for i in range(1,10):
            # change_or_not = input("If everyhing is right press enter, otherwise write n:")
            # if change_or_not == "n":
            whatchange = -1
            while restart_loop:
                print("--------------------------")
                if whatchange == -1:
                    whatchange = input("What to change? \n0 = overflight or not, \n1 = minimal distance time, \n2 = arr dep, \n3 = mark this flight as unusable\n-1 change nothing \n:")
                    try:
                        whatchange = int(whatchange)
                    except:
                        whatchange = -1
                if whatchange == 0:
                    # overflight_changed = int(input("Change overflight to: (0 = no overflight 1 = overflight)"))
                    overflight_ornot_new = -1
                    if overflight_ornot == 0:
                        overflight_ornot_new = 1
                        text_overflight = "OVERFLIGHT"
                    if overflight_ornot == 1:
                        overflight_ornot_new = 0
                        text_overflight = "NO OVERFLIGHT"
                    print(f"Change overflight from {overflight_ornot} to {overflight_ornot_new}")
                    overflight_ornot = overflight_ornot_new
                    plt.title(f"{text_overflight}  flight {flight_ident}, {arr_dep}, group {group_this}, distance {np.round(minimal_distance_meters)}m,angle {np.round(angle_flight_at_minimal_distance_degrees[0])}deg ")
                    plt.draw()
                if whatchange == 1:
                    print(f"Discard info on overflight distance and point {minimal_distance_meters, point_minimal_distance}")
                    minimal_distance_meters, point_minimal_distance = np.nan, np.nan
                    for i in range(0,10):
                        minimal_distance_time_changed = input("Can you tell the overflight time in the picture by the extension of the black dots? (0 = cannot say out of image, other = seconds after last point in gpx): ")
                        try:
                            minimal_distance_time_changed = float(minimal_distance_time_changed)
                            break
                        except:
                            print("The input was not readable")

                    if minimal_distance_time_changed == "0":
                        print(f"discarded also time minimal distance {datetime.datetime.strftime(datetime.datetime.fromtimestamp(int(round(time_minimal_distance)), tz=pytz.UTC),'%H:%M:%S')}")
                        time_minimal_distance = np.nan
                    else:
                        time_minimal_distance_new = time_minimal_distance + minimal_distance_time_changed#datetime.timedelta(seconds = minimal_distance_time_changed)
                        print(minimal_distance_time_changed, time_minimal_distance_new)
                        print(f"Change time of minimal distance by {minimal_distance_time_changed} s from{datetime.datetime.strftime(datetime.datetime.fromtimestamp(int(round(time_minimal_distance)), tz=pytz.UTC),'%H:%M:%S')} to {datetime.datetime.strftime(datetime.datetime.fromtimestamp(int(round(time_minimal_distance_new)), tz=pytz.UTC),'%H:%M:%S')}")
                        time_minimal_distance = time_minimal_distance_new
                        changed_overflighttime = 1

                if whatchange == 2:
                    change_arrdep_to = 1
                    if arr_dep == "arrivals":
                        print(f"I changed the flights arrdep from {arr_dep} to departures")
                    if arr_dep == "departures":
                        print(f"I changed the flights arrdep from {arr_dep}  to arrivals")
                    print(f"Discard info on overflight distance and point {minimal_distance_meters, point_minimal_distance}")
                    minimal_distance_meters, point_minimal_distance, time_minimal_distance = np.nan, np.nan, np.nan
                if whatchange == 3:
                    usable = 0
                    print(f"I labeld this flight as usable {usable}")
                    minimal_distance_meters, point_minimal_distance, time_minimal_distance = np.nan, np.nan, np.nan

                exit_question = input("Was this all? I yes press enter, else:\n0 = overflight or not, \n1 = minimal distance time, \n2 = arr dep, \n3 = mark this flight as unusable\n:")

                if exit_question == "":
                    restart_loop = False
                    change_or_not = ""
                    break
                else:
                    whatchange = int(exit_question)
        axis_gps.clear()

    try:
        time_minimal_distance = datetime.datetime.fromtimestamp(int(round(time_minimal_distance)), tz=pytz.UTC)
    except:
        pass
    print(f"Overflight time: {time_minimal_distance}\nMinimal distance: {minimal_distance_meters}")
    return time_minimal_distance,minimal_distance_meters,point_minimal_distance, overflight_ornot, usable, change_arrdep_to, changed_overflighttime


def save_to(filepath,data,date):
    for x in range(0, 5):
        try:
            print(
                f"Saving the of day {date.astype('datetime64[D]').astype(str)} to {filepath}")
            data.to_csv(filepath)
            break
        except Exception as error:
            input(f"Not able to save: {error}\nMaybe resource is blocked, close is and press enter to try again.")



# find out overflight times out of gps data
parentdir = params.parentdir
savedir = params.flightsprocessed_dir
files_processed = savedir + f"\\*processed*.csv"

plot_all = False
save_files = True
print("Processing step 0")


print(f"Processing the data of dates {params.selected_dates.astype('datetime64[D]').astype(str)}")
conseq_number = 0

# load in data
for date in params.selected_dates:
    # date = params.selected_dates[0]
    print(f"Processing the data of on day: {date.astype('datetime64[D]').astype(str)}")
    flights = pd.DataFrame([])
    #read in flights
    # first try to load cache, if this doesnot work load not cached data
    filenames_flights_processed = np.array(glob.glob(files_processed, recursive=True))
    filenames_flights_processed, last_version = params.get_file_date_and_last_version(filenames_flights_processed,[date])


    print("Try loading  processed flight data .")
    flights = readinflights.read_in_data_of_one_file(filenames_flights_processed, processed = True)

    if flights == 0:
        flights = pd.DataFrame([])
        print("Could not already processed flight data load raw flight data.")
        columns_to_hold = ['ident', 'fa_flight_id', 'operator', 'origin', 'destination', 'actual_off', 'actual_on','aircraft_type']
        for arr_dep in ["arrivals","departures"]:
            files_raw = parentdir + f"\\flights\\*{arr_dep}*.csv"
            filenames_flights_raw = np.array(glob.glob(files_raw, recursive=True))
            filenames_flights_raw = np.array([x for x in filenames_flights_raw if ('sched' not in x) and ('fr24' not in x)])
            filenames_flights_raw, last_version_raw = params.get_file_date_and_last_version(filenames_flights_raw, [date])
            try:
                print("Try raw flight data .")
                flights_arr_dep = readinflights.read_in_data_of_one_file(filenames_flights_raw, processed = False)
                flights_arr_dep = flights_arr_dep[columns_to_hold]
                flights_arr_dep["arr_dep"] = arr_dep
                flights = pd.concat([flights,flights_arr_dep])
            except:
                print("Could not load flight data")

    flights= flights.reset_index(drop=True)
    #make new columns for the information we want to gather in this step
    flights[["overflight_group", "min_dist_time", "min_dist_m","changed_overflight_time", "usable", "overflight_from","changed_arr_dep"]] = np.nan

    savepaths = os.path.join(savedir,f"{date.astype('datetime64[D]').astype(str)}_flights_processed_{last_version+1}.csv")
    print(f"Set safepaths: {savepaths}")
    change_arr_dep = pd.DataFrame(columns = flights.columns)

    filenames_tracks = np.array(glob.glob(parentdir + "\\flights\\tracks\\*", recursive=True))

    tracks = readinflights.read_in_tracks_of_multiples_days(filenames_tracks, [date])
    aircraft_types = pd.read_csv(params.aircrafttype_fp)

    plt.show(block = False)

    fig4, ax_gps = plt.subplots(1)
    arr_dep_other = {"arrivals":"departures", "departures":"arrivals"}

    # first run through all flights then through the changed
    for processing_step in ['flights','arrdep_changed']:
        print(f"processing {processing_step}")
        for arr_dep,group,default_time in zip(["arrivals", "departures"],[1,2],["actual_on","actual_off"]):
        # arr_dep = "arrivals"
            conseq_number_arrdep = 0
            print(f"------------------------- \nprocessing {arr_dep} of {date}")
            if processing_step == 'flights':
                flights_arr_dep = flights[flights.arr_dep == arr_dep]
            elif processing_step == 'arrdep_changed':
                flights_arr_dep = flights[(flights.arr_dep == arr_dep)&(flights.changed_arr_dep == 1)]
            for index,row in flights_arr_dep.iterrows():
                if processing_step == "arrdep_changed":
                    print(f"---------------------\n({conseq_number_arrdep}/{flights_arr_dep.shape[0]-1}), flight {row.ident} {arr_dep} at actual_off/actual_on: {row.actual_off}/{row.actual_on}")
                else:
                    print(f"---------------------\n({conseq_number_arrdep}/{flights_arr_dep.shape[0]-1}), flight {row.ident} {arr_dep} at actual_off/actual_on:  {row.actual_off}/{row.actual_on}")
                flight_ident = row.ident

                if flight_ident in tracks.keys():
                    print("We have a track for this flight")
                    track_this = tracks[flight_ident]
                    times_UNIX = (track_this.timestamp.dt.tz_localize(None) - pd.Timestamp(
                        "1970-01-01")) // pd.Timedelta('1s')
                    ref_point = [47.262463, 11.369862, 590] # 577 + 20 m
                    try:
                        time_minimal_distance,minimal_distance_meters,point_minimal_distance, overflight_ornot, usable, change_arr_dep_to, changed_overflight_time = gps_points_processing(np.array(track_this.latitude), np.array(track_this.longitude), np.array(track_this.altitude_m), np.array(times_UNIX) ,ref_point, arr_dep, flight_ident, 500,ax_gps, plot_all)
                    except:
                        print("Couldnot process gps")
                        time_minimal_distance, minimal_distance_meters, point_minimal_distance, overflight_ornot, usable, change_arr_dep_to, changed_overflight_time =np.nan, np.nan, np.nan,np.nan, np.nan, np.nan,np.nan
                    print(overflight_ornot,time_minimal_distance)
                    if change_arr_dep_to == 0:
                        flights.loc[index, "usable"] = usable
                        if overflight_ornot:
                            group_this = group
                            flights.loc[index, "overflight_group"] = group_this
                            flights.loc[index, "changed_overflight_time"]= changed_overflight_time
                            flights.loc[index, "min_dist_time"] = time_minimal_distance
                            if arr_dep == "arrivals":
                                flights.loc[index, "overflight_from"] = 90
                            elif arr_dep == "departures":
                                flights.loc[index, "overflight_from"] = 270
                            flights.loc[index, "min_dist_m"] = minimal_distance_meters
                        else:
                            group_this = 2 + group
                            flights.loc[index, "overflight_group"] = group_this
                            flights.loc[index, "min_dist_time"] = row[default_time]

                    else:
                        if processing_step == 'flights':
                            change_arr_dep_this = row
                            change_arr_dep_this["arr_dep"] = arr_dep_other[arr_dep]
                            change_arr_dep_this["changed_arr_dep"] = 1
                            flights = flights.drop(index)
                            print(f"dropping row out of {arr_dep} data.")

                            flights = pd.concat([flights,change_arr_dep_this.to_frame(name = index).T])
                            # print(f"change arr dep {change_arr_dep}")
                            print(f"{arr_dep} -> {arr_dep_other[arr_dep]} adding row \n:{flights.loc[index]} to change_arr_dep")



                else:
                    overflightgroup = 4+group
                    print(f"We donot have a track this flight is overflight group {overflightgroup}")
                    flights.loc[index,"overflight_group"] = overflightgroup
                    flights.loc[index, "min_dist_time"] = row[default_time]

                conseq_number += 1
                conseq_number_arrdep += 1
                # save every 10th entry
                if conseq_number_arrdep % 10 == 0:
                    if save_files:
                        save_to(savepaths, flights, date)



    flights = flights.sort_values(by='min_dist_time', ignore_index=True)
    if save_files:
        save_to(savepaths, flights, date)


