import numpy as np
import re
import glob
import pandas as pd
import os

parent_dir = "F:\\Uniarbeit 23_11_09\\data\\Data_airport\\Data_airport"
selected_dates = np.array(["2023-12-01"], dtype='datetime64[D]')

def read_in_data_of_one_day(parentdir, date):
    filedir = os.path.join(parentdir, "analysis\\Times_overflights")

    filenames = np.array(glob.glob(filedir + "\\*", recursive=True))
    dates = np.array(
        [re.search(re.compile(r'\d{4}-\d{2}-\d{2}'), path).group() for path in filenames],
        dtype='datetime64[D]')
    data = {}
    filenames_of_the_date_selected = filenames[dates == date.astype('datetime64[D]')]
    for arrdep in ["arrivals","departures"]:
        filenames_of_the_date_selected_arrdep = np.array([path for path in filenames_of_the_date_selected if arrdep in path.lower()])
        print(f"Reading in overflightdata of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_of_the_date_selected_arrdep}")
        try:
            df = pd.read_csv(filenames_of_the_date_selected_arrdep[0], index_col=0, header=0)
            df.Start = pd.to_datetime(df.Start, utc=True).dt.tz_convert('Europe/Berlin')
            df.End = pd.to_datetime(df.End, utc=True).dt.tz_convert('Europe/Berlin')
            data[arrdep] = df
        except:
            print(f"Could not read in overflights {filenames_of_the_date_selected_arrdep}")
            return 0
    return data