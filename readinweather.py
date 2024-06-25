import numpy as np
import re
import glob
import pandas as pd
import os



def read_in_data_of_one_day(filedir, date):

    filenames = np.array(glob.glob(filedir + "\\*weather_data*", recursive=True))
    dates = np.array(
        [re.search(re.compile(r'\d{4}-\d{2}-\d{2}'), path).group().replace("_", "-") for path in filenames],
        dtype='datetime64[D]')

    filenames_of_the_date_selected = filenames[dates == date.astype('datetime64[D]')]
    print(f"Reading in weather data of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_of_the_date_selected}")

    try:
        df = pd.read_csv(filenames_of_the_date_selected[0], index_col=0, header=0)
        df["Time"] = pd.to_datetime(df.Time_UNIX, unit = "s").dt.tz_localize('UTC')
        df.Temperature = (df.Temperature - 32)/1.8
        df["Dew Point"] = (df["Dew Point"] - 32)/1.8
        df["Wind Speed"] = df["Wind Speed"] * 1.60934
        df["Wind Gust"] = df["Wind Gust"] * 1.60934
        df["Wind Dir"] = df["Wind Dir"].apply(winddir_to_numb)

    except:
        print(f"Could not read in {filenames_of_the_date_selected}")
        return 0
    df.index = df.Time
    return df

def winddir_to_numb(wind_dir_string):
    winddir = np.nan
    lookup_dict = {"West":270,
                   "South":180,
                   "North":0,
                   "East":90,
                   "NW":315,
                   "NE":45,
                   "SE":135,
                   "SW":225,
                   "NNW":337.5,
                   "NNE":22.5,
                   "ENE":67.5,
                   "ESE":112.5,
                   "SSE":157.5,
                   "SSW":202.5,
                   "WSW":247.5,
                   "WNW":292.5}
    if wind_dir_string in lookup_dict:
        winddir = lookup_dict[wind_dir_string]
    return winddir

def read_in_data_of_muliple_days(filedir, dates):
    data = pd.DataFrame()
    for date in dates:
        filenames = np.array(glob.glob(filedir + "\\*weather_data*", recursive=True))
        dates_weather = np.array(
            [re.search(re.compile(r'\d{4}-\d{2}-\d{2}'), path).group().replace("_", "-") for path in filenames],
            dtype='datetime64[D]')

        filenames_of_the_date_selected = filenames[dates_weather == date.astype('datetime64[D]')]
        print(f"Reading in weather data of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_of_the_date_selected}")

        try:
            df = pd.read_csv(filenames_of_the_date_selected[0], index_col=0, header=0)
            df["Time"] = pd.to_datetime(df.Time_UNIX, unit = "s").dt.tz_localize('UTC')
            df.Temperature = (df.Temperature - 32)/1.8
            df["Dew Point"] = (df["Dew Point"] - 32)/1.8
            df["Wind Speed"] = df["Wind Speed"] * 1.60934
            df["Wind Gust"] = df["Wind Gust"] * 1.60934
            df["Wind Dir"] = df["Wind Dir"].apply(winddir_to_numb)
            data = pd.concat([data,df])
            data.index = data.Time



        except:
            print(f"Could not read in {filenames_of_the_date_selected}")
    return data