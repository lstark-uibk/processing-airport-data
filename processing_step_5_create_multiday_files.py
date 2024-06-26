import matplotlib.pyplot as plt
import pandas as pd
import datetime
import params
import numpy as np
import glob
import readinflights
# import readinmicrophone
import readinpartector
# import readinweather
import os

savedirflights = params.flightsprocessed_dir
flightfiles = savedirflights + f"\\*processed*.csv"
savedir_multiday = os.path.join(params.flightsprocessed_dir,"multiday_processing")
savedirpart = params.partprocessed_dir

startdate = params.selected_dates[0]
enddate = params.selected_dates[-1]

flights = pd.DataFrame([])
partector_data = pd.DataFrame([])
for date in params.selected_dates:
    # first try to load cache, if this doesnot work load not cached data
    filenames_flights_processed = np.array(glob.glob(flightfiles, recursive=True))
    filenames_flights_processed, last_version = params.get_file_date_and_last_version(filenames_flights_processed, [date])
    try:
        flights_this = readinflights.read_in_data_of_one_file(filenames_flights_processed,   processed=True)

    except:
        print("Could not load flight data")

    window_size = "10s"
    # micro_this = readinmicrophone.read_in_data_of_multiple_days(os.path.join(params.parentdir, "microphone"),[date])
    partector_data_this = readinpartector.read_in_data_of_multiple_days(os.path.join(params.parentdir, "partector"),[date], params.partector_nr)
    flights = pd.concat([flights, flights_this], ignore_index=True)
    # micro = pd.concat([micro, micro_this])
    partector_data = pd.concat([partector_data, partector_data_this])



fp_flights = os.path.join(savedir_multiday,f"all_flights_{startdate}_till_{enddate}.csv")
save = input(f"-------------------------\nSave multiday flights \n {fp_flights}(y/n)")
if (save == "y" ):

    print(f"Save multiday flights data to\n{fp_flights}")
    flights.to_csv(fp_flights)

fp_numbers_all = os.path.join(savedir_multiday,f"all_partectordata_number_{startdate}_till_{enddate}.csv")
fp_diameters_all = os.path.join(savedir_multiday,f"all_partectordata_diameter_{startdate}_till_{enddate}.csv")
save_part = input(f"Save the partector data in multiday file to \n{fp_numbers_all}\n {fp_diameters_all}")
if save_part == "y":
    partector_data['particle_number_concentration'].to_csv(fp_numbers_all)
    partector_data['average_particle_diameter'].to_csv(fp_diameters_all)