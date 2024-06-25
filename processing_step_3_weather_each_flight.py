import numpy as np
import glob
import os
import pandas as pd
import params
import readinflights
import readinweather


savedir = params.flightsprocessed_dir
flightfiles = savedir + f"\\*processed*.csv"
save_files = True

for date in params.selected_dates:
    filenames_flights_processed = np.array(glob.glob(flightfiles, recursive=True))
    filenames_flights_processed, last_version = params.get_file_date_and_last_version(filenames_flights_processed, [date])

    flights = readinflights.read_in_data_of_one_file(filenames_flights_processed,processed=True)
    weather = readinweather.read_in_data_of_one_day(os.path.join(params.parentdir, "weather"), date)
    windspeed_lim = 2
    for index,row in flights.iterrows():
        start = row.min_dist_time
        end = row.min_dist_time + pd.Timedelta(minutes=30)
        weatheraround = weather[start:end]
        weathermean = weatheraround.mean()
        weathermean = weathermean.rename(index={'Time': 'Time_mean_weather'})
        windgroup = 0
        if weathermean["Wind Speed"] < windspeed_lim:
            windgroup = 0
        else:
            if 0 < weathermean["Wind Dir"] < 180:
                windgroup = 1
            else:
                windgroup = 2

        weathermean["Wind_group"] = windgroup

        for name,value in weathermean.items():
            flights.loc[index,name] = value
    if save_files:

        savepath = os.path.join(savedir, f"{date.astype('datetime64[D]').astype(str)}_flights_processed_{last_version + 1}.csv")
        print(f"Save to: {savepath}")
        flights.to_csv(savepath)


def get_wind_group(flights,weather):
    for index, row in flights.iterrows():
        start = row.min_dist_time
        end = row.min_dist_time + pd.Timedelta(minutes=30)
        weatheraround = weather[start:end]
        weathermean = weatheraround.mean()
        weathermean = weathermean.rename(index={'Time': 'Time_mean_weather'})
        windspeed_lim = 2
        windgroup = 0
        if weathermean["Wind Speed"] < windspeed_lim:
            windgroup = 0
        else:
            if 0 < weathermean["Wind Dir"] < 180:
                windgroup = 1
            else:
                windgroup = 2

        weathermean["Wind_group"] = windgroup

        for name, value in weathermean.items():
            flights.loc[index, name] = value
        return flights
