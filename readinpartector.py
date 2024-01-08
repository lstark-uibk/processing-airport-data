import numpy as np
import re
import glob
import pandas as pd
import os



def read_in_data_of_one_day(parentdir, date):
    filedir = os.path.join(parentdir, "partector")

    filenames_partector = np.array(glob.glob(filedir + "\\*partector*", recursive=True))
    dates_partector = np.array(
        [re.search(re.compile(r'\d{4}_\d{2}_\d{2}'), path).group().replace("_", "-") for path in filenames_partector],
        dtype='datetime64[D]')

    print(f"Reading in partectordata of the day: {date.astype('datetime64[D]').astype(str)}")
    data = []
    filenames_partector_of_the_date_selected = filenames_partector[dates_partector == date.astype('datetime64[D]')]
    try:
        df = pd.read_csv(filenames_partector_of_the_date_selected[0], index_col=None, header=0)
        df["_time"] = pd.to_datetime(df['_time'], utc=True).dt.tz_convert('Europe/Berlin')
        data = df
    except:
        print(f"Could not read in {filenames_partector_of_the_date_selected}")
        return 0
    return data

