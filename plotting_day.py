import os.path
import datetime
import readinflights
import readinpartector
import readinweather
import readinmicrophone
import readinoverflights
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates
from windrose import WindroseAxes, plot_windrose
import pandas as pd

plotting_only_overflights = True
plotting_whole_day = False
subtract_bg = True
parent_dir = "F:\\Uniarbeit 23_11_09\\data\\Data_airport\\Data_airport"
selected_dates = np.array(["2023-12-04"], dtype='datetime64[D]')
# arr_dep = "departures"
arr_dep = "arrivals"
start_date = np.datetime64('2023-11-22')
end_date = np.datetime64('2023-11-25')
# selected_dates = np.arange(start_date, end_date, dtype='datetime64[D]')
# Times_overflights_visible = Times_overflights[Times_overflights.spikevisible == 1]

flights = readinflights.read_in_data_of_one_day(parent_dir, selected_dates)
partector_data = readinpartector.read_in_data_of_one_day(parent_dir, selected_dates)
weather = readinweather.read_in_data_of_one_day(parent_dir,selected_dates)
micro = readinmicrophone.read_in_data_of_one_day(parent_dir,selected_dates)
Time_overflights = readinoverflights.read_in_data_of_one_day(parent_dir, selected_dates)
Time_overflights["departures"] = Time_overflights["departures"].sort_values(by="Start",ignore_index=True)
Time_overflights["arrivals"] = Time_overflights["arrivals"].sort_values(by="Start",ignore_index=True)
Airplaneinfos = pd.read_csv(os.path.join(parent_dir,"analysis\\Aircraft_type.csv"))

flights[arr_dep] = flights[arr_dep][~np.isnan(flights[arr_dep].near_overflight)]
nr_flights = Time_overflights[arr_dep].shape[0]


# Create a 3x3 grid with different column widths
fig = plt.figure(figsize=(10, 6))
gs = GridSpec(nr_flights, 3, width_ratios=[1, 0.2, 0.2], hspace=0.5)


if plotting_only_overflights:
    print("Plotting only overflights")

    # flight = flights[arr_dep].iloc[0]
    for index, times in Time_overflights[arr_dep].iterrows():

        print(f"Flight {times.Flight}")
        if arr_dep == "departures":
            times.End = times.End + datetime.timedelta(minutes = 5)
        partector_this = partector_data.loc[(times.Start < partector_data["_time"]) & (partector_data["_time"] < times.End)]
        bg_part_this = partector_this.loc[(times.Start < partector_data["_time"]) & (partector_data["_time"] < times.Start + datetime.timedelta(seconds=90))]
        bg_part_this_mean = bg_part_this[["average_particle_diameter","particle_number_concentration","particle_mass","ldsa"]].mean(axis = 0)
        print(f"subtracting backgrounds {bg_part_this_mean}")
        mic_this = micro.loc[(times.Start < micro.Time) & (micro.Time < times.End)]
        ax_lines = fig.add_subplot(gs[index, 0])
        ax_lines2 = ax_lines.twinx()
        ax_lines3 = ax_lines.twinx()
        if subtract_bg:
            particle_number_concentration_bg_cor = partector_this.particle_number_concentration - bg_part_this_mean.particle_number_concentration
            ax_lines.plot((partector_this._time - times.Start).dt.total_seconds()/60 ,particle_number_concentration_bg_cor)
            ax_lines2.plot((partector_this._time - times.Start).dt.total_seconds()/60 ,partector_this.average_particle_diameter - bg_part_this_mean.average_particle_diameter, color = "C1")
        else:
            ax_lines.plot((partector_this._time - times.Start).dt.total_seconds()/60 ,partector_this.particle_number_concentration)
            ax_lines2.plot((partector_this._time - times.Start).dt.total_seconds() / 60, partector_this.average_particle_diameter, color="C1")
        integral_bg_corr =  np.trapz(particle_number_concentration_bg_cor, (partector_this._time - times.Start).dt.total_seconds())
        print(f"integrated: {format(integral_bg_corr, '.3e')}")
        ax_lines3.plot((mic_this.Time - times.Start).dt.total_seconds()/60 ,mic_this.Amplitude, color = "C2")
        ax_lines3.spines['right'].set_position(('outward', 30))  # Adjust the position of the third y-axis

        ax_lines.set_title(f"Starttime: {datetime.datetime.strftime(times.Start,'%H:%M:%S')} flight {times.Flight}, number BG corr integrated: {format(integral_bg_corr, '.3e')} 1/cm^3")
        if index < nr_flights-1:
            ax_lines.xaxis.set_visible(False)
            ax_lines.set_xlabel("Normalized time referenced to start of airplane")

        try:
            ax_Windir = fig.add_subplot(gs[index, 1])
            weatherdata_this = weather.loc[(times.Start - datetime.timedelta(minutes = 10) < weather.Time) & (weather.Time < times.End + datetime.timedelta(minutes = 10))]
            # Draw the arrow
            ax_Windir.text(0.5, 0.7, weatherdata_this["Wind Dir"].mode()[0], ha='center', va='center', fontsize=12, color='black')
            ax_Windir.text(0.5, 0.2, f"{round(weatherdata_this['Wind Speed'].mean(),2)} m/s", ha='center', va='center', fontsize=12, color='black')
            ax_Windir.set_xlim(0, 1)
            ax_Windir.set_ylim(0, 1)
            ax_Windir.axis('off')

        except:
            ax_Windir.axis('off')




        try:
            ax_plane = fig.add_subplot(gs[index, 2])
            aircraft_type = flights[arr_dep][flights[arr_dep].ident == times.Flight].aircraft_type
            thisplane = Airplaneinfos[Airplaneinfos.airplane_type == aircraft_type.values[0].replace(" ","")]
            ax_plane.text(0.5, 0.7, f"engine: {thisplane.engine.values[0]}" , ha='center', va='center', fontsize=12,
                           color='black')
            ax_plane.text(0.5, 0.2, f"type: {thisplane.airplane_group.values[0]}", ha='center', va='center',
                           fontsize=12, color='black')
            ax_plane.set_xlim(0, 1)
            ax_plane.set_ylim(0, 1)
            ax_plane.axis('off')
        except:
            ax_plane.axis('off')

fig.suptitle(f"Flights {arr_dep} of the day {selected_dates.astype(str)[0]}")

# plt.title(f"Flights of the day {selected_dates.astype(str)[0]}")
# plt.tight_layout()
plt.show()
# #
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# from windrose import WindroseAxes
#
# def plot_windrose(ax, direction, speed, title):
#     ax.bar(direction, speed, normed=True, opening=0.8, edgecolor='white')
#     ax.set_title(title)
#
# # Sample data
# np.random.seed(42)
# nr_flights = 5
# Wind_Dir = np.array([1,2,3])
# Wind_Speed =  np.array([3,4,5])
#
# # Create subplots
# fig, axes = plt.subplots(nr_flights, 1, figsize=(10, 5 * nr_flights), subplot_kw={'projection': 'windrose'})
# plt.subplots_adjust(hspace=0.5)

# # Plot windrose for each flight
# for index, ax in enumerate(axes):
#     plot_windrose(ax, Wind_Dir, Wind_Speed, title=f'Flight {index + 1}')
#
# # Show the plot
# plt.show()
# #

if plotting_whole_day:
    print("Plotting")

    fig, ax = plt.subplots(1)

    near_overflights  ={}
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

# if plotting_only_overfligh