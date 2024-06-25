import datetime
import numpy as np
import math
import glob
import os
import pandas as pd
import params
import readinflights

savedir = params.flightsprocessed_dir
flightfiles = savedir + f"\\*processed*.csv"
save_files = True

for date in params.selected_dates:
    files_processed = params.flightsprocessed_dir + f"\\*processed*.csv"
    filenames_flights_processed = np.array(glob.glob(flightfiles, recursive=True))
    filenames_flights_processed, last_version = params.get_file_date_and_last_version(filenames_flights_processed, [date])

    flights = readinflights.read_in_data_of_one_file(filenames_flights_processed,processed=True)
    aircraft_types = pd.read_csv(params.aircrafttype_fp)

    for index,row in flights.iterrows():
        if not pd.isnull(row.aircraft_type):
            info_on_aircraft = aircraft_types[aircraft_types.airplane_type == row.aircraft_type.replace(" ", "")]
            print(f"Aircraft type {row.aircraft_type}:\nInfo: {info_on_aircraft}")
            if not pd.isnull(info_on_aircraft.values).all():
                for column, entry in info_on_aircraft.items():
                    flights.loc[index, column] = entry.values[0]

    if save_files:
        savepath = os.path.join(savedir, f"{date.astype('datetime64[D]').astype(str)}_flights_processed_{last_version + 1}.csv")
        print(f"Save to: {savepath}")

        flights.to_csv(savepath)

def get_aircraft_models(flights,aircraft_types):
    for index, row in flights.iterrows():
        if not pd.isnull(row.aircraft_type):
            info_on_aircraft = aircraft_types[aircraft_types.airplane_type == row.aircraft_type.replace(" ", "")]
            print(f"Aircraft type {row.aircraft_type}:\nInfo: {info_on_aircraft}")
            if not pd.isnull(info_on_aircraft.values).all():
                for column, entry in info_on_aircraft.items():
                    flights.loc[index, column] = entry.values[0]
    return flights


