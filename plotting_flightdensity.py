import pandas as pd
import matplotlib.pyplot as plt
import params
import numpy as np
import  os
import matplotlib.dates as mdates
from matplotlib.dates import DateFormatter

dates = params.selected_dates
flights = pd.read_csv(os.path.join(params.flightsprocessed_dir,"multiday_processing\\all_flights_2024-02-06_till_2024-02-29.csv"),index_col=0)
time_columns = ['min_dist_time', 'max_peak_start','max_peak']
for col in time_columns:
    try:
        flights[col] = pd.to_datetime(flights[col])
    except:
        print(f"cannot parse {col} to datetime")

flights =flights.reset_index(drop=True)
rolling_avg = "1h"

flightdensity = pd.DataFrame([])


for group in [1,2,3,4]:
    flights_arr_dep = flights[flights.overflight_group == group]
    flights_times = pd.Series(flights_arr_dep.min_dist_time)
    all_seconds = pd.DataFrame(0,index=pd.date_range(start=params.selected_dates[0], end=params.selected_dates[-1]+ np.timedelta64(1, 'D'), freq='s').tz_localize('UTC'),columns = ["density"])
    overlap = all_seconds.index.isin(flights_times)
    all_seconds[overlap] = 1
    flightdensity[group] = all_seconds.rolling(window=rolling_avg).mean() * 3600

flightdensity["all"] = flightdensity.sum(axis = 1)
flightdensity_low_res = flightdensity.iloc[::100]
fig, ax = plt.subplots()

bottom = np.zeros(24)
for group,c,label in zip([1,2,3,4],["C0","C1","C2","C3"],["arrival from east","departure to east","arrival from west","departure to west"]):
    flights_of_group = flights[flights.overflight_group == group]
    flights_days_of_group =  flights_of_group.groupby(pd.Grouper(key='min_dist_time', freq='D'))
    flights_per_day_of_group = flights_days_of_group.ident.count()
    print(group,flights_per_day_of_group)


    bar_width = 1/24*10
    plt.bar(flights_per_day_of_group.index,flights_per_day_of_group,bar_width,bottom= bottom,color=c,label=label)
    bottom = bottom + flights_per_day_of_group.values


midday_times = pd.date_range(start='2024-02-01 12:00', end='2024-03-01 12:00', freq='D')
for midday in midday_times:
    plt.axvline(midday, color='gray', linewidth=0.6, alpha=0.7)
ax.grid(axis="y")
twax = ax.twinx()
flights_days = flights.groupby(pd.Grouper(key='min_dist_time', freq='D'))
flights_per_day = flights_days.ident.count()
flights_big_airplanes_per_day = flights[flights.airplane_group_1_fanover50ps_2fanunder50ps_3propeller == 1].groupby(
    pd.Grouper(key='min_dist_time', freq='D')).ident.count()
flights_small_airplanes_per_day = flights[(flights.airplane_group_1_fanover50ps_2fanunder50ps_3propeller == 2) | (
            flights.airplane_group_1_fanover50ps_2fanunder50ps_3propeller == 3)].groupby(
    pd.Grouper(key='min_dist_time', freq='D')).ident.count()
flights_no_info = flights[(flights.airplane_group_1_fanover50ps_2fanunder50ps_3propeller == 0)].groupby(
    pd.Grouper(key='min_dist_time', freq='D')).ident.count()

rat_small_big = (flights_small_airplanes_per_day/(flights_small_airplanes_per_day+flights_big_airplanes_per_day))
twax.plot(flights_small_airplanes_per_day.index,rat_small_big,c="black",label="fraction of small airplanes (lower than 30 persons capacity)")
twax.set_ylim(0,1)
twax.axhline(rat_small_big.mean(),c="black",linestyle= "--")
twax.legend()
ax.legend(loc=2)
plt.show()
date_format = DateFormatter('%m-%d %H')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%d.%m.'))
ax.xaxis.set_major_locator(mdates.DayLocator())
twax.tick_params('x', rotation=45)
ax.tick_params('x', rotation=45)
