import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib  import cm
import matplotlib.dates as mdates
import re
import pytz
import params
import pytz
import h5py
from scipy.interpolate import interp1d
import datetime
from matplotlib.dates import DateFormatter

#make this for many days
dates = params.selected_dates
# onedate_selected = np.array([datetime.date(2024,2,15),datetime.date(2024,2,16),datetime.date(2024,2,17),datetime.date(2024,2,18)], dtype='datetime64')
onedate_selected = params.selected_dates
dates_set = set(onedate_selected)
parent_fp = params.flightsprocessed_dir

# flights = pd.read_csv(os.path.join(parent_fp,"all_flights_2024-02-10_till_2024-02-10.csv"),index_col=0)
flights = pd.read_csv(os.path.join(parent_fp,"multiday_processing\\all_flights_2024-02-06_till_2024-02-23.csv"),index_col=0)
numbers = pd.read_csv(os.path.join(params.partprocessed_dir, "all_partectordata_number_2024-02-06_till_2024-02-23.csv"), index_col=0)
diameters = pd.read_csv(os.path.join(params.partprocessed_dir, "all_partectordata_diameter_2024-02-06_till_2024-02-23.csv"), index_col=0)
time_columns = ['scheduled_out',
                'estimated_out', 'actual_out', 'scheduled_off', 'estimated_off',
                'actual_off', 'scheduled_on', 'estimated_on', 'actual_on',
                'scheduled_in', 'estimated_in', 'actual_in', 'min_dist_time', 'start_usable', 'end_usable','time_peak_0',
                'time_peak_1', 'time_peak_2', 'time_peak_3', 'time_peak_4','max_peak_start','max_peak']
for col in time_columns:
    try:
        flights[col] = pd.to_datetime(flights[col])
    except:
        print(f"cannot parse {col} to datetime")
# flights.loc[pd.isnull(flights.airplane_group_1_fanover50ps_2fanunder50ps_3propeller),"airplane_group_1_fanover50ps_2fanunder50ps_3propeller"]= 0
for index, row in flights.loc[pd.isnull(flights.overflight_group)].iterrows():
    if row.arr_dep == "arrivals":
        flights.loc[index,"overflight_group"] = 5
    elif row.arr_dep == "departures":
        flights.loc[index,"overflight_group"] = 6
flights = flights[flights.min_dist_time.dt.date.isin(dates_set)]
print(flights)
print("Load partector data")

partector_data = pd.concat([numbers,diameters],axis = 1)
partector_data = partector_data.dropna()
partector_data.index = pd.to_datetime(partector_data.index)
# partector_data = partector_data[np.isin(partector_data.index.date,onedate_selected)]
partector_data_raw = partector_data.copy()
smooth_part = partector_data[["average_particle_diameter", "particle_number_concentration"]].rolling(30).mean()
partector_data = smooth_part
low_res = 30
partector_data_high_res = partector_data
partector_data = partector_data.iloc[::low_res]
partector_data = partector_data.dropna()

fig2, ax = plt.subplots(1)
ax2 = ax.twinx()

x_label_spikes = 150
labels = ["overflight arr", "overflights dep", "no overflight arr", "no overflight dep", "no info arr",
          "no info dep"]
# plot peak specs
for index, flight_with_peak in flights[flights['prominent_peak_with_no_flights_between'] == 1].iterrows():
    xleft = flight_with_peak.max_peak_start
    xright = flight_with_peak.max_peak_start + pd.Timedelta(seconds=flight_with_peak.max_peak_width_s)
    xmax = flight_with_peak.max_peak
    nearest_index = np.abs((partector_data.index - xmax).values).argmin()
    ymax = partector_data["particle_number_concentration"].iloc[nearest_index]
    ax.hlines((1 - 0.95) * ymax, xmin=xleft, xmax=xright, color='C3', linewidth=2)
    ax.vlines(x=xmax, ymin=(1 - 0.95) * ymax, ymax=ymax, color="C3", linewidth=2)
    ax.text(xmax, ymax, f"{index}", rotation=70)
# plot other flights
ax2.vlines(flights["min_dist_time"][~pd.isnull(flights["min_dist_time"])], 150, 170,
           colors="C2", linewidth=2, zorder=100)
for index, row in flights.iterrows():
    ax2.text(pd.to_datetime(row["min_dist_time"]), 150,
             f"{index}: ({round(row.overflight_group)}/{round(row.airplane_group_1_fanover50ps_2fanunder50ps_3propeller)}/{round(row.Wind_group)})",
             rotation=70, zorder=100, fontsize=9)
ax.set_yscale("log")
ax.legend(loc=3)
ax2.legend(loc=4)

plt.show()