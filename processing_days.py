import os.path
import datetime
import readinflights
import readinpartector
import readinweather
import readinmicrophone
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

plotting_whole_day = False
plotting_only_overflights = True
parent_dir = "F:\\Uniarbeit 23_11_09\\data\\Data_airport\\Data_airport"
selected_dates = np.array(["2023-12-04"], dtype='datetime64[D]')
start_date = np.datetime64('2023-11-22')
end_date = np.datetime64('2023-11-25')
# selected_dates = np.arange(start_date, end_date, dtype='datetime64[D]')
# Times_overflights = pd.read_csv(os.path.join(parent_dir,"analysis\\Times_overflights_arrivals.csv"),skipinitialspace=True, parse_dates = ['Start', 'End'], index_col=None)
# Times_overflights_visible = Times_overflights[Times_overflights.spikevisible == 1]

flights = readinflights.read_in_data_of_one_day(parent_dir, selected_dates)
partector_data = readinpartector.read_in_data_of_one_day(parent_dir, selected_dates)
weather = readinweather.read_in_data_of_one_day(parent_dir,selected_dates)
micro = readinmicrophone.read_in_data_of_one_day(parent_dir,selected_dates)

threshold = 50000
# Find indices where the values surpass the threshold upwards
crossings = partector_data.particle_number_concentration.gt(threshold) & ~partector_data.particle_number_concentration.shift().gt(threshold)
crossings_times = partector_data._time[crossings]


Times_overflights_df = pd.DataFrame(columns=["Flight","Start","End","spikevisible"])
for arr_dep in ["arrivals","departures"]:
    for index,flight in flights[arr_dep][~np.isnan(flights[arr_dep].near_overflight)].iterrows():
        if arr_dep == "arrivals":
            best_time = pd.to_datetime(flight.actual_on, utc=True)
        elif arr_dep == "departures":
            best_time = pd.to_datetime(flight.actual_off, utc=True)
        print(f"flight {flight.ident}")
        leeway =  5
        leeway_before = best_time - pd.Timedelta(minutes=leeway)
        leeway_after = best_time + pd.Timedelta(minutes=leeway)

        # Boolean indexing to check if there is data within the specified time range
        crossing_exists = (
                (crossings_times >= leeway_before) &
                (crossings_times <= leeway_after)
        )
        spikevisible= 0
        if crossing_exists.any():
            spikevisible = 1
            #for this flight we have a spike
            crossing_this_flight = crossings_times[crossing_exists].iloc[0]
            before = crossing_this_flight - pd.Timedelta(minutes=2)
            after = crossing_this_flight + pd.Timedelta(minutes=7)
            print("This flight has a spike")
        else:
            print("No spike")
            before = best_time - pd.Timedelta(minutes=2)
            after = best_time + pd.Timedelta(minutes=7)
        data_this = partector_data.loc[(before < partector_data["_time"]) & (partector_data["_time"] < after)]
        if plotting_only_overflights:
            fig, ax = plt.subplots(1)
            ax2 = ax.twinx()
            ax.plot(data_this["_time"] - before, data_this.average_particle_diameter)
            ax2.plot(data_this["_time"] - before, data_this.particle_number_concentration, color = "C1")
            ax.legend(["diameter"])
            ax2.legend(["number"])
            plt.title(f"{flight.ident} from {datetime.datetime.strftime(before,'%H:%M')} to {datetime.datetime.strftime(after,'%H:%M')}")
            plt.show()
            while plt.get_fignums():
                plt.pause(0.1)
        alldatathisflight = pd.DataFrame([[flight.ident,before,after,spikevisible]],columns=["Flight","Start","End","spikevisible"])
        Times_overflights_df = pd.concat([Times_overflights_df,alldatathisflight], ignore_index=True)

    Times_overflights_df.to_csv(os.path.join(parent_dir,f"analysis\\Times_overflights\\{selected_dates[0].astype(str)}_Times_overflights_{arr_dep}.csv"))
    Times_overflights_df = pd.DataFrame(columns=["Flight", "Start", "End", "spikevisible"])


if plotting_whole_day:
    print("Plotting")

    fig, ax = plt.subplots(1)
    for time in crossings_times:
        print(time)
        string = f"{time.strftime('%H:%M:%S')} 2 min before = {(time- pd.Timedelta(minutes = 2)).strftime('%H:%M:%S')}, 5 min after =  {(time+ pd.Timedelta(minutes = 5)).strftime('%H:%M:%S')}"
        ax.axvline(x=time, color='C3')
        ax.text(time, 1, string, rotation=90)

    near_overflights  ={}
    for arr_dep in ["arrivals", "departures"]:
        near_overflights[arr_dep] = flights[arr_dep][~np.isnan(flights[arr_dep].near_overflight)]
        for index, row in near_overflights[arr_dep].iterrows():
            if arr_dep == "arrivals":
                best_time = pd.to_datetime(row.actual_on, utc=True)
                string = f"{best_time.strftime('%H:%M')} Flug {row.ident}  2 min before = {(best_time- pd.Timedelta(minutes = 2)).strftime('%H:%M:%S')}, 5 min after =  {(best_time+ pd.Timedelta(minutes = 5)).strftime('%H:%M:%S')}"
                ax.axvline(x=best_time, color='tab:green')
            if arr_dep == "departures":
                best_time = pd.to_datetime(row.actual_off, utc=True)
                string = f"{best_time.strftime('%H:%M')} Flug {row.ident}  2 min before = {(best_time- pd.Timedelta(minutes = 2)).strftime('%H:%M:%S')}, 5 min after =  {(best_time+ pd.Timedelta(minutes = 5)).strftime('%H:%M:%S')}"
                ax.axvline(x=best_time, color='tab:pink')
            ax.text(best_time, 1, string, rotation=90)
    ax2 = ax.twinx()
    ax.plot(partector_data["_time"], partector_data.average_particle_diameter, color = "C1")
    ax2.plot(partector_data["_time"], partector_data.particle_number_concentration)
    plt.show()

# if plotting_only_overflights:
#     fig, ax = plt.subplots(2)
#     for index, row in Times_overflights_visible.iterrows():
#         data_this = partector_data.loc[(row.Start < partector_data["_time"]) & (partector_data["_time"] < row.End)]
#         ax[0].plot(data_this["_time"] - row.Start, data_this.average_particle_diameter)
#         ax[1].plot(data_this["_time"] - row.Start, data_this.particle_number_concentration)
#     plt.show()