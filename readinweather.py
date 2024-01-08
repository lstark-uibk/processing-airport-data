import numpy as np
import re
import glob
import pandas as pd
import os



def read_in_data_of_one_day(parentdir, date):
    filedir = os.path.join(parentdir, "weather")

    filenames = np.array(glob.glob(filedir + "\\*weather_data*", recursive=True))
    dates = np.array(
        [re.search(re.compile(r'\d{4}-\d{2}-\d{2}'), path).group().replace("_", "-") for path in filenames],
        dtype='datetime64[D]')

    filenames_of_the_date_selected = filenames[dates == date.astype('datetime64[D]')]
    print(f"Reading in weather data of the day: {date.astype('datetime64[D]').astype(str)} in {filenames_of_the_date_selected}")

    try:
        df = pd.read_csv(filenames_of_the_date_selected[0], index_col=0, header=0)
        df["Time"] = pd.to_datetime(df.Time_UNIX, unit = "s").dt.tz_localize('UTC').dt.tz_convert('Europe/Berlin')
        df.Temperature = (df.Temperature - 32)/1.8
        df["Dew Point"] = (df["Dew Point"] - 32)/1.8
        df["Wind Speed"] = df["Wind Speed"] * 1.60934
        df["Wind Gust"] = df["Wind Gust"] * 1.60934

    except:
        print(f"Could not read in {filenames_of_the_date_selected}")
        return 0
    return df

