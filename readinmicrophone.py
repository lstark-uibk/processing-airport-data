import numpy as np
import re
import glob
import pandas as pd
import os
import params

parent_dir = params.parentdir
selected_dates = np.array(["2023-11-29"], dtype='datetime64[D]')


def read_in_data_of_one_day(filedir, date):

    filenames = np.array(glob.glob(filedir + "\\*", recursive=True))
    dates = np.array(
        [re.search(re.compile(r'\d{4}_\d{2}_\d{2}'), path).group().replace("_", "-") for path in filenames],
        dtype='datetime64[D]')


    filenames_of_the_date_selected = filenames[dates == date.astype('datetime64[D]')]
    print(f"Reading in Microphone of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_of_the_date_selected}")
    data = pd.DataFrame()
    try:
        for fp in filenames_of_the_date_selected:
            df = pd.read_csv(fp, index_col=0, header=0)
            df["Time"] = pd.to_datetime(df['Time_UNIX'], unit = "s").dt.tz_localize('UTC').dt.tz_convert('Europe/Berlin')
            data = pd.concat([data,df])
            data = data.sort_values(by = "Time_UNIX")
    except:
        print(f"Could not read in {filenames_of_the_date_selected}, is there no data for this time?")
        return 0
    return data

def read_in_data_of_multiple_days(filedir, dates):
    data = pd.DataFrame()
    for date in dates:
        filenames = np.array(glob.glob(filedir + "\\*", recursive=True))
        dates_mic = np.array(
            [re.search(re.compile(r'\d{4}_\d{2}_\d{2}'), path).group().replace("_", "-") for path in filenames],
            dtype='datetime64[D]')


        filenames_of_the_date_selected = filenames[dates_mic == date.astype('datetime64[D]')]
        print(f"Reading in Microphone of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_of_the_date_selected}")

        try:
            for fp in filenames_of_the_date_selected:
                df = pd.read_csv(fp, index_col=0, header=0)
                df["Time"] = pd.to_datetime(df['Time_UNIX'], unit = "s").dt.tz_localize('UTC')
                data = pd.concat([data,df])
                data = data.sort_values(by = "Time_UNIX")
                data.index = data.Time
        except:
            print(f"Could not read in {filenames_of_the_date_selected}, is there no data for this time?")
            return 0

    return data

