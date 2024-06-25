import numpy as np
import re
import glob
import pandas as pd
import os
import params
import traceback
import sys
parent_dir = params.parentdir
selected_dates = np.array(["2023-11-29"], dtype='datetime64[D]')


def read_in_data_of_one_day(filedir, date, processed = False):

    flights = {}

    for arr_dep in ["arrivals","departures"]:
        arr_dep_files = np.array(glob.glob(filedir + f"\\*{arr_dep}*", recursive=True))
        dates = np.array(
            [re.search(re.compile(r'\d{4}-\d{2}-\d{2}'), path).group() for path in arr_dep_files],
            dtype='datetime64[D]')


        filenames_of_the_date_selected = arr_dep_files[dates == date.astype('datetime64[D]')]
        print(f"Reading in flight {arr_dep} of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_of_the_date_selected}")
        data = pd.DataFrame()
        for fp in filenames_of_the_date_selected:
            try:
                if processed:
                    df = pd.read_csv(fp, header=0, index_col=0)
                else: df = pd.read_csv(fp, header=0)
                time_columns = ['scheduled_out',
           'estimated_out', 'actual_out', 'scheduled_off', 'estimated_off',
           'actual_off', 'scheduled_on', 'estimated_on', 'actual_on',
           'scheduled_in', 'estimated_in', 'actual_in']
                if processed:
                    time_columns = ["overflight_time"]
                    df.index = pd.to_datetime(df.index)
                df[time_columns] = df[time_columns].apply(pd.to_datetime)
                if not processed:
                    if arr_dep == "arrivals":
                        index = df["actual_on"][~pd.isnull(df.actual_on)]
                        index[pd.isnull(df.actual_on)]= df.index[pd.isnull(df.actual_on)]
                        df.index = index
                    else:
                        index = df["actual_off"][~pd.isnull(df.actual_on)]
                        index[pd.isnull(df.actual_on)]= df.index[pd.isnull(df.actual_on)]
                        df.index = index

                data = pd.concat([data,df])
                data = data.sort_index()

            except:
                print(f"Could not read in {filenames_of_the_date_selected}")
                return 0
        flights[arr_dep] = data
    return flights

def read_in_data_of_one_file(file, processed = False):
    print(f"Read in filenames {file}")
    data = pd.DataFrame()
    fp = file
    try:
        if processed:
            df = pd.read_csv(fp, header=0, index_col = 0)
        else:
            df = pd.read_csv(fp, header=0)
        time_columns = ['scheduled_out',
   'estimated_out', 'actual_out', 'scheduled_off', 'estimated_off',
   'actual_off', 'scheduled_on', 'estimated_on', 'actual_on',
   'scheduled_in', 'estimated_in', 'actual_in', 'min_dist_time']
        for col in time_columns:
            try:
                df[col] = pd.to_datetime(df[col],format='mixed')
            except:
                print(f"cannot parse {col} to datetime")
        df = df.reset_index(drop=True)
        data = pd.concat([data,df])

    except:
        print(f"Could not read in flights in {fp}")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        # Print the error message
        print(f"Error: {exc_value}")

        # Print the stack trace
        traceback.print_tb(exc_traceback)
        return 0
    return data
def read_in_data_of_muliple_days(files, dates, index_column = "actual_on", processed = False):
    data = pd.DataFrame()
    for date in dates:
        dates_flights = np.array(
            [re.search(re.compile(r'\d{4}-\d{2}-\d{2}'), path).group() for path in files],
            dtype='datetime64[D]')


        filenames_of_the_date_selected = files[dates_flights == date.astype('datetime64[D]')]
        print(f"Reading in flights of the days: {date.astype('datetime64[D]').astype(str)} in {filenames_of_the_date_selected}")

        for fp in filenames_of_the_date_selected.tolist():
            try:
                if processed:
                    df = pd.read_csv(fp, header=0, index_col = 0)
                else:
                    df = pd.read_csv(fp, header=0)
                time_columns = ['scheduled_out',
           'estimated_out', 'actual_out', 'scheduled_off', 'estimated_off',
           'actual_off', 'scheduled_on', 'estimated_on', 'actual_on',
           'scheduled_in', 'estimated_in', 'actual_in', 'overflight_time','start_usable','end_usable']
                for col in time_columns:
                    try:
                        df[col] = pd.to_datetime(df[col])
                    except:
                        print(f"cannot parse {col} to datetime")
                df = df.reset_index(drop=True)
                data = pd.concat([data,df])
            except:
                print(f"Could not read in {filenames_of_the_date_selected}")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                # Print the error message
                print(f"Error: {exc_value}")

                # Print the stack trace
                traceback.print_tb(exc_traceback)
                return 0
    return data


def read_in_tracks_of_multiples_days(files, dates):
    print(f"Reading in tracks of the days: {dates}")  # in {filenames_tracks_of_the_date_selected}")

    for date in dates:
        date_tracks = np.array(
            [re.search(re.compile(r'\d{4}-\d{2}-\d{2}'), path).group() for path in files],
            dtype='datetime64[D]')
        filenames_tracks_of_the_date_selected = files[date_tracks == date.astype('datetime64[D]')]


    tracks = {}

    flight_names_tracks = [re.search(re.compile(r'([A-Z0-9-]+)\.csv'), path).group(1) for path in filenames_tracks_of_the_date_selected]
    for filename, flight in zip(filenames_tracks_of_the_date_selected,flight_names_tracks):
        print(f"Read in track of flight {flight} in {filename}")
        try:
            df = pd.read_csv(filename, index_col=None, skiprows=52, header=0, comment = '#',parse_dates=['timestamp'])
            index_repeat = df[(df == df.columns).all(axis=1)].index.min()      # get index of first iteration of the header
            if not pd.isna(index_repeat):
                df = df[0:index_repeat]
                df = df.apply(pd.to_numeric, errors='ignore')
                df.timestamp = pd.to_datetime(df.timestamp)
            if "altitude" in df.columns:
                print("change altitude to altitude_m")
                df = df.rename(columns={"altitude": "altitude_m"})
            if "groundspeed" in df.columns:
                print("change groundspeed to groundspeed_mps")
                df = df.rename(columns={"groundspeed": "groundspeed_mps"})
            tracks[flight] = df
        except:
            print(f"Couldnot read in track {filename}")
    return tracks