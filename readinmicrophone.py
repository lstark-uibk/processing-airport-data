import numpy as np
import re
import glob
import pandas as pd
import os

parentdir = "F:\\Uniarbeit 23_11_09\\data\\Data_airport\\Data_airport"
selected_dates = np.array(["2023-11-29"], dtype='datetime64[D]')


def read_in_data_of_one_day(parentdir, date):
    filedir = os.path.join(parentdir, "microphone")

    filenames = np.array(glob.glob(filedir + "\\*", recursive=True))
    dates = np.array(
        [re.search(re.compile(r'\d{4}_\d{2}_\d{2}'), path).group().replace("_", "-") for path in filenames],
        dtype='datetime64[D]')


    filenames_of_the_date_selected = filenames[dates == date.astype('datetime64[D]')]
    print(f"Reading in partectordata of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_of_the_date_selected}")
    data = pd.DataFrame(columns=["Unnamed: 0","Time_UNIX","Amplitude"])
    try:
        for fp in filenames_of_the_date_selected:
            df = pd.read_csv(fp, index_col=0, header=0)
            df["Time"] = pd.to_datetime(df['Time_UNIX'], unit = "s").dt.tz_localize('UTC').dt.tz_convert('Europe/Berlin')
            data = pd.concat([data,df])
            data = data.sort_values(by = "Time_UNIX")
    except:
        print(f"Could not read in {filenames_of_the_date_selected}")
        return 0
    return data

