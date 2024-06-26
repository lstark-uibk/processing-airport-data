import numpy as np
import os
import pytz
import glob
import re

parentdir = "C:\\Users\\Umwelt\\Documents\\Data local\\Data_airport"
# parentdir = "F:\\Uniarbeit 23_11_09\\data\\Data_airport\\Data_airport"
flightsprocessed_dir =  os.path.join(parentdir, "analysis\\Processed_flights")
# flightsprocessed_dir = "D:\\Uniarbeit 23_11_09\\data\\test\\flights_processed"
partprocessed_dir = os.path.join(parentdir, "analysis\\Processed_partector")
# partprocessed_dir = "D:\\Uniarbeit 23_11_09\\data\\test\\flights_processed"
micsprocessed_dir =  os.path.join(parentdir, "analysis\\Processed_microphone")

aircrafttype_fp =  os.path.join(parentdir, "analysis\\Aircraft_type.csv")
day_notes_fp =  os.path.join(parentdir, "analysis\\infos_on_days\\Notes_on_days.csv")
selected_dates = np.array(["2024-02-04"], dtype='datetime64[D]')
start_date = np.datetime64('2024-02-05')
end_date = np.datetime64('2024-02-06')
# start_date = np.datetime64('2024-04-30')
# end_date = np.datetime64('2024-05-01')
selected_dates = np.arange(start_date, end_date, dtype='datetime64[D]')
# selected_dates = np.array(["2024-02-07","2024-02-08","2024-02-11"], dtype='datetime64[D]')
# selected_dates = np.array(["2024-03-06"], dtype='datetime64[D]')

# selected_dates = np.array(["2024-02-06"], dtype='datetime64[D]')
# selected_dates = np.array(["2023-12-02"], dtype='datetime64[D]')

partector_nr = 8300

def get_multiple_filenames_flights(filedir, ending):
    filenames = {}
    for arr_dep in ["arrivals", "departures"]:
        filename_with_widcard_arrdep = filedir + f"\\*{arr_dep}*"+ending
        print(filename_with_widcard_arrdep)
        filenames[arr_dep] = np.array(glob.glob(filename_with_widcard_arrdep, recursive=True))
    return filenames


def get_file_date_and_last_version(files, dates):
    filenames_of_the_date_selected_max_versions = []
    lastversions = []
    for date in dates:
        dates_files = np.array(
            [re.search(re.compile(r'\d{4}-\d{2}-\d{2}'), path).group() for path in files],
            dtype='datetime64[D]')


        filenames_of_the_date_selected = files[dates_files == date.astype('datetime64[D]')]
        if filenames_of_the_date_selected.size == 0:
            return np.nan, -1
        # print(f"Get last version of the day {date}")
        versions_date_selected = np.array([int(re.search(r'_(\d).csv', file).group(1)) if re.search(r'_\d.csv', file) else np.nan for file in filenames_of_the_date_selected])

        index_max_version = np.argmax(versions_date_selected)
        lastversion = versions_date_selected[index_max_version]

        filenames_of_the_date_selected_max_version = filenames_of_the_date_selected[index_max_version]
        # print(f"Take last version: {lastversion}, {filenames_of_the_date_selected_max_version} {date}")
        filenames_of_the_date_selected_max_versions.append(filenames_of_the_date_selected_max_version)
        lastversions.append(lastversion)
    return filenames_of_the_date_selected_max_version, lastversion
