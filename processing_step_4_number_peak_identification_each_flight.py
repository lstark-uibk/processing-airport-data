# with this script you can read the information on the peaks of the partector
# then you can add this information to the flights and make a new flights_processed_file a new flights_pocessed file with a new version number

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
import  os
from scipy.signal import find_peaks, peak_widths, peak_prominences


#read in data of the days
savedir = params.flightsprocessed_dir
flightfiles = savedir + f"\\*processed*.csv"
save_files = True

plotmode = 0
i = 40
j = 50
# 0... plot the peaks around flights i to j
# 1... plot the peak around flight i
# 2... no plotting only peak fitting



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


flights["prominent_peak_with_no_flights_between"] = 0

def plot_single_flight_and_calc_max(i,ax,ax2,block=True,plot=True):
    before_overflight = 10
    after_overflights = 40
    all_seconds = np.arange(-60 * before_overflight, 60 * after_overflights + 1)
    if i <0:
        i=0
    row = flights.loc[i]
    print(f"({i}/{flights.shape[0]}) flight {i} {row.ident}, {row.min_dist_time}, windgroup {row.Wind_group}")
    numbers_this_ex = False
    timebefore_overflight = row.min_dist_time- datetime.timedelta(minutes=before_overflight)
    timeafter_overflight = row.min_dist_time + datetime.timedelta(minutes=after_overflights)
    try:
        numbers_this =  partector_data[timebefore_overflight:timeafter_overflight].particle_number_concentration
        numbers_this = np.log10(numbers_this)
        ref_index = (numbers_this.index - row.min_dist_time).total_seconds().astype(int)
        numbers_this.index = ref_index
        if numbers_this.size > 0:
            numbers_this_ex = True
        # diam_this = partector_data[timebefore_overflight:timeafter_overflight].average_particle_diameter
        # diam_this.index = ref_index
        # interpolate
        numbers_this = pd.Series(np.interp(all_seconds, ref_index, numbers_this),index=all_seconds)
        # diam_this = pd.DataFrame(np.interp(all_seconds, ref_index, diam_this),index=all_seconds)

    except: "No numbers for this flight"
    if numbers_this_ex:
        ax.clear()
        ax2.clear()
        numbers_this = numbers_this.rolling(window=40).mean()
        min_dist_time_this = row.min_dist_time

        for group, delay in zip([1, 2, 3, 4, 5, 6], [0, 20, 100, 100, 0, 20]):
            if group == row.overflight_group:
                look_for_peaks = numbers_this.loc[delay:]
                delay_to_look_after = delay
        #find out peak infomation
        rel_height = 0.95
        #now with lower prominence, look that we include also a second peak if the second is way higher than the first and there is also no peak between th first and the second
        peaks, info = find_peaks(look_for_peaks, distance=60 * 3, prominence=0.1, height=np.log10(10000), rel_height=rel_height)

        # peak index in reltime
        # gives widths and locations (like it woul be when x = [0,1,2,3...]
        widths, widths_heights, left, right = peak_widths(look_for_peaks, peaks, rel_height=rel_height)
        prominences, _, _ = peak_prominences(look_for_peaks, peaks)
        contour = numbers_this.iloc[peaks] - prominences
        # the find peaks takes the delay to look after as the 0, so to get the peaks in rel time we have to add this
        peaks += delay_to_look_after
        left += delay_to_look_after
        right += delay_to_look_after


        # check whether there are any other flights between this flight and the next peak and then select the highest peak
        otherflights_in_range = flights[(min_dist_time_this - pd.Timedelta(minutes=10) < flights.min_dist_time) & (
                min_dist_time_this + pd.Timedelta(minutes=40) > flights.min_dist_time) & (
                                                    flights.min_dist_time != row.min_dist_time)]
        otherflights_in_range_rel_time = (
                    otherflights_in_range["min_dist_time"] - min_dist_time_this).dt.total_seconds()
        # only flights after can contribute to peaks
        projected_plumetime_other_flights = otherflights_in_range_rel_time[otherflights_in_range_rel_time > 0]
        # the flights are preselected to peak length
        projected_plumetime_other_flights.loc[(otherflights_in_range.overflight_group == 1)] += 60
        projected_plumetime_other_flights.loc[(otherflights_in_range.overflight_group == 2)] += 60
        projected_plumetime_other_flights.loc[(otherflights_in_range.overflight_group == 3)] += 60 * 10
        projected_plumetime_other_flights.loc[(otherflights_in_range.overflight_group == 4)] += 60 * 10
        projected_plumetime_other_flights.loc[(otherflights_in_range.overflight_group == 5)] += 60
        projected_plumetime_other_flights.loc[(otherflights_in_range.overflight_group == 6)] += 60
        if projected_plumetime_other_flights.size > 0:
            first_flight_after = projected_plumetime_other_flights.min()
        else:
            first_flight_after = numbers_this.index[-1]
        peaks = np.array(peaks)
        left = np.array(left)
        widths = np.array(widths)
        peaks_until_next_flight = peaks[np.array(peaks) < first_flight_after]


        if peaks_until_next_flight.size > 0:
            first_maximum_peak_index = 0
            if len(peaks_until_next_flight) < 3:
                first_maximum_peak_index = numbers_this[peaks_until_next_flight].argmax()
            for j in range(0, len(peaks_until_next_flight) - 1):
                if (j == 0) and look_for_peaks[peaks_until_next_flight[j]] > look_for_peaks[ peaks_until_next_flight[j + 1]]:
                    first_maximum_peak_index = j
                    break
                if look_for_peaks[peaks_until_next_flight[j]] > look_for_peaks[peaks_until_next_flight[j - 1]] and \
                        look_for_peaks[peaks_until_next_flight[j]] > \
                        look_for_peaks[peaks_until_next_flight[j + 1]]:
                    first_maximum_peak_index = j
                    break

            first_max_peak_start = left[first_maximum_peak_index]
            first_max_peak = peaks[first_maximum_peak_index]
            first_max_peak_width = widths[first_maximum_peak_index]
            flights.loc[i,"prominent_peak_with_no_flights_between"] = 1
            flights.loc[i,"max_peak_start"] = row.min_dist_time + pd.Timedelta(seconds = first_max_peak_start)
            flights.loc[i,"max_peak"] = row.min_dist_time + pd.Timedelta(seconds = first_max_peak)
            flights.loc[i,"max_peak_width_s"] = first_max_peak_width


        if plot:
            title = f"flight {row.ident} at {row.min_dist_time}\noverflight group {row.overflight_group}, airplane group {row.airplane_group_1_fanover50ps_2fanunder50ps_3propeller}, windgroup {row.Wind_group} "


            # ax2.plot(numbers_this.index, numbers_this, label = f"flight {row.ident} at {row.min_dist_time} windgroup {row.Wind_group} otherflights between {otherflights_between} peak start delay {round(firstpeak_start)}")


            # ax.plot(diam_this,c="C1")
            ax2.plot(numbers_this.index, numbers_this,c="C0")
            ax2.axvline(0, linewidth=0.5, c="k")
            #other lines plot
            ax.vlines((otherflights_in_range["min_dist_time"] - min_dist_time_this).dt.total_seconds(), 150, 170,
                       colors="C2", linewidth=2, zorder=100)
            for index, row in otherflights_in_range.iterrows():
                ax.text((row["min_dist_time"]- min_dist_time_this).total_seconds(), 150,
                         f"{index}: ({round(row.overflight_group)}/{round(row.airplane_group_1_fanover50ps_2fanunder50ps_3propeller)}/{round(row.Wind_group)})",
                         rotation=70, zorder=100, fontsize=9)
            if peaks_until_next_flight.size > 0:
                title += f", prominentpeak with no other flights interfering {flights.loc[i,'prominent_peak_with_no_flights_between']}\npeak start {round(first_max_peak_start)}s/{flights.loc[i,'max_peak_start']}, peak max {round(first_max_peak)}s/{flights.loc[i,'max_peak_width_s']}, peak width {round(flights.loc[i,'max_peak_width_s'])}"
                #plot peak parameters
                ax2.hlines(widths_heights[first_maximum_peak_index], xmin=left[first_maximum_peak_index], xmax=right[first_maximum_peak_index],color='C3', linewidth = 2)
                ax2.vlines(x=peaks[first_maximum_peak_index], ymin=contour.iloc[first_maximum_peak_index], ymax=numbers_this.loc[peaks[first_maximum_peak_index]], color="C3",linewidth = 2)
            else:
                title += f", NO PEAK"
            # peak parameters plot
            ax2.hlines(widths_heights, xmin=left, xmax=right,color='C3',linewidth = 0.5)
            ax2.vlines(x=numbers_this.loc[peaks].index, ymin=contour, ymax=numbers_this.loc[peaks], color="C3",linewidth = 0.5)
            fig.suptitle(title)
        plt.show(block=block)
        plt.pause(0.1)

fig, ax = plt.subplots()
ax2 = ax.twinx()
############to skip through several flights starting with index i uncomment this
if plotmode == 0:
    while i < j:
        if i >= flights.shape[0]:
            break
        plotted = plot_single_flight_and_calc_max(i,ax,ax2,block = False)
        next = input("Next? (a to go back)")
        if next == 'a':
            print("Back")
            i+=-1
        else:
            print("Forth")
            i+=1
############# to plot only one flight of index i uncomment this
if plotmode == 1:
    i=184
    plotted = plot_single_flight_and_calc_max(i,ax,ax2)
############# to process all flights with no visual check uncomment this
if plotmode == 2:
    for i in range(flights.shape[0]):
        plot_single_flight_and_calc_max(i,ax,ax2,plot=False)
if save_files:
    savepath = os.path.join(savedir, f"{date.astype('datetime64[D]').astype(str)}_flights_processed_{last_version + 1}.csv")
    print(f"Save to: {savepath}")

    flights.to_csv(savepath)

#make a plot with all flights:
# fig, axs = plt.subplots(5,1,sharex=True,sharey=True)
# for index, row in x.iterrows():
#
#     numbers_this = numbers[str(row["index"])]
#     numbers_this_ex = True
#     diam_this = diameters[str(row["index"])]
#     ax2[index] = axs[index].twinx()
#     axs[index].plot(diam_this, c="C1")
#
#     title = f"flight {row.ident} at {row.min_dist_time} ({row.overflight_group}/{row.airplane_group_1_fanover50ps_2fanunder50ps_3propeller}/{row.Wind_group}) peak start {round(firstpeak_start)}s, peak max {firstpeakafter}, peak width {round(firstpeak_width)}s"
#     axs[index].set_title(title)
#     ax2[index].plot(numbers_this.index, numbers_this, c="C0")
#     ax2[index].axvline(0, linewidth=0.5)
#     labels = ["overflight arr", "overflights dep", "no overflight arr", "no overflight dep", "arrivals no gps",
#               "departures no gps"]
#     otherflights_in_range = flights[(row.min_dist_time - pd.Timedelta(minutes=10) < flights.min_dist_time) & (
#             row.min_dist_time + pd.Timedelta(minutes=40) > flights.min_dist_time) & (
#                                             flights.min_dist_time != row.min_dist_time)]
#
#     for group, label, color, linestyle in zip([1, 2, 3, 4, 5, 6], labels,
#                                               ["C1", "C2", "C1", "C2", "C1", "C2"],
#                                               ["-", "-", "--", "--", ":", ":"]):
#         flights_this_group = otherflights_in_range[otherflights_in_range.overflight_group == group]
#         otherflights_in_range_rel_time = (otherflights_in_range["min_dist_time"] - row.min_dist_time).dt.total_seconds()
#         if flights_this_group.size > 0:
#             axs[index].vlines(otherflights_in_range_rel_time, 40, 70,
#                               colors=color, linestyle=linestyle, linewidth=2,
#                               label=f"group {group}: {label}", zorder=100)
#         if row.overflight_group == group:
#             axs[index].vlines(0, 40, 70, colors=color,
#                               linestyle=linestyle, linewidth=2,
#                               label=f"group {group}: {label}", zorder=100)
#     start_time = (row["first_peak_start"] - row.min_dist_time).total_seconds()
#     end_time = start_time + row["first_peak_width_s"]
#     ax2[index].hlines(1000, xmin=start_time, xmax=end_time,
#                       color='C3')  # Convert indices to integers
#
#     peak_time = (row["first_peak_max"] - row.min_dist_time).total_seconds()
#     ax2[index].vlines(x=peak_time, ymin=0, ymax=numbers_this.loc[int(peak_time)], color="C3")
# plt.show()




