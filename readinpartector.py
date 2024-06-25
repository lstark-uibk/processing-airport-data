import numpy as np
import re
import glob
import pandas as pd
import os
import params
import sys
import traceback

def read_in_data_of_one_day(filedir, date,partector_nr):

    filenames_partector = np.array(glob.glob(filedir + f"\\*partector*{partector_nr}*", recursive=True))
    dates_partector = np.array(
        [re.search(re.compile(r'\d{4}_\d{2}_\d{2}'), path).group().replace("_", "-") for path in filenames_partector],
        dtype='datetime64[D]')
    filenames_partector_of_the_date_selected = filenames_partector[dates_partector == date.astype('datetime64[D]')]

    print(f"Reading in partectordata of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_partector_of_the_date_selected}")
    data = []
    try:
        df = pd.read_csv(filenames_partector_of_the_date_selected[0], index_col=None, header=0)
        try:
            df["_time"] = pd.to_datetime(df['_time'], utc=True,format='mixed')
        except:
            df["_time"] = pd.to_datetime(df['_time'], utc=True)
        data = df
        data.index = data["_time"]
    except:
        print(f"Could not read in {filenames_partector_of_the_date_selected}")
        exc_type, exc_value, exc_traceback = sys.exc_info()
        # Print the error message
        print(f"Error: {exc_value}")

        # Print the stack trace
        traceback.print_tb(exc_traceback)
        return 0

    return data

def read_in_data_of_multiple_days(filedir, dates,partector_nr):
    data = pd.DataFrame()
    for date in dates:
        filenames_partector = np.array(glob.glob(filedir + f"\\*partector*{partector_nr}*", recursive=True))
        dates_partector = np.array(
            [re.search(re.compile(r'\d{4}_\d{2}_\d{2}'), path).group().replace("_", "-") for path in filenames_partector],
            dtype='datetime64[D]')
        filenames_partector_of_the_date_selected = filenames_partector[dates_partector == date.astype('datetime64[D]')]

        print(f"Reading in partectordata of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_partector_of_the_date_selected}")
        for filename_partector_of_the_date_selected in filenames_partector_of_the_date_selected:
            try:
                df = pd.read_csv(filename_partector_of_the_date_selected, index_col=None, header=0)
                try:
                    df["_time"] = pd.to_datetime(df['_time'], utc=True, format='mixed')
                except:
                    df["_time"] = pd.to_datetime(df['_time'], utc=True)
                data = pd.concat([data,df])
                data.index = data["_time"]

            except:
                print(f"Could not read in {filenames_partector_of_the_date_selected}")
                print(f"Could not read in {filenames_partector_of_the_date_selected}")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                # Print the error message
                print(f"Error: {exc_value}")

                # Print the stack trace
                traceback.print_tb(exc_traceback)
                return 0

    return data

