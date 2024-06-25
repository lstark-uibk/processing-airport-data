import matplotlib.pyplot as plt
import pandas as pd
import datetime
import params
import numpy as np
import glob
import readinflights
import readinmicrophone
import readinpartector
import readinweather
import  os
parent_fp = "D:\\Uniarbeit 23_11_09\\data\\Data_airport\\Data_airport\\analysis\\Processed_partector\\currently_using"
numbers = pd.read_csv(os.path.join(parent_fp,"partectordata_flights_numbers_2024-02-06_till_2024-02-28.csv"),index_col=0)
diameters = pd.read_csv(os.path.join(parent_fp,"partectordata_flights_diamters_2024-02-06_till_2024-02-28.csv"),index_col=0)
flights = pd.read_csv(os.path.join(parent_fp,"all_flights_2024-02-06_till_2024-02-28.csv"),index_col=0)
time_columns = ['scheduled_out',
                'estimated_out', 'actual_out', 'scheduled_off', 'estimated_off',
                'actual_off', 'scheduled_on', 'estimated_on', 'actual_on',
                'scheduled_in', 'estimated_in', 'actual_in', 'min_dist_time', 'start_usable', 'end_usable']
for col in time_columns:
    try:
        flights[col] = pd.to_datetime(flights[col])
    except:
        print(f"cannot parse {col} to datetime")

before_overflight = 10
after_overflights = 40
# differntiated between overflight group airplane group and windgroup
plume_range = {1:{1:{0:[30,1500],
                     1:[20,600],
                     2:[20,1000]},
                  2: {0: [80, 400],
                      1: [0, 0],
                      2: [100, 400]},
                  3:{0:[80,400],
                     1:[0,0],
                     2:[100,400]}},
               2:{1:{0:[30,1500],
                     1:[20,600],
                     2:[20,1000]
               }},
               3: {1: {0: [250, 1000],
                       1: [0, 0],
                       2: [250, 1000]
                       }},
               4: {1: {0: [30, 1500],
                       1: [20, 600],
                       2: [20, 1000]
                       }}
               }
time_day_groups = {0:[0,10],
                   1:[10,14],
                   2:[14,23]
                   }
all_seconds = np.arange(-60 * before_overflight, 60 * after_overflights + 1)
check_whetherflights_after_minutes = 15
check_whetherflights_before_minutes = 5
mask_no_flights_after = pd.Series(False, index=flights.index)
select_overflight_group = 1
select_plane_group = 1
select_plane_group_2 = select_plane_group
wind_cutoff = 2
for index, row in flights.iterrows():
    time_before = row.min_dist_time  - pd.Timedelta(minutes=check_whetherflights_before_minutes)
    time_after = row.min_dist_time + pd.Timedelta(minutes=check_whetherflights_after_minutes)
    flights_after_checked = (time_before < flights.min_dist_time)&(time_after > flights.min_dist_time)&(row.min_dist_time != flights.min_dist_time)

    # print(time_before,time_after)
    # print(flights[flights_after_checked].min_dist_time)
    # print("_----------------------")
    any_flights_after = flights_after_checked.any()
    if not any_flights_after:
        # print(index, any_flights_after)
        mask_no_flights_after.loc[index] = True

def mutliwind_old():
    fig, axs = plt.subplots(3,1, sharex=True)
    ax = axs[0]
    ax2 = axs[2]
    select_overflight_group = 1
    select_plane_group = 1
    select_plane_group_2 = select_plane_group
    wind_cutoff = 2


    for windgroup,label in zip([0,1,2],[f"Wind < {wind_cutoff}m/s",f"> {wind_cutoff}m/s wind dir from eastern halve",f"> {wind_cutoff}m/s wind dir from western halve"]):
        axs[windgroup].axvline(0,color = "k")
        mask_plane =  (flights.airplane_group_1_fanover50ps_2fanunder50ps_3propeller == select_plane_group)#|(flights.airplane_group == select_plane_group_2)
        mask_overflight = (flights.overflight_group == select_overflight_group)
        mask_wind = (flights.Wind_group == windgroup)
        mask = mask_plane & mask_wind & mask_overflight & mask_no_flights_after
        mask_indices =  mask[mask].index.astype(str)
        windgroup_numbers = numbers.loc[:,mask_indices]
        windgroup_diameters = diameters.loc[:,mask_indices]
        if windgroup_numbers.size>0:
            plume_range_this = plume_range[select_overflight_group][select_plane_group][windgroup]
            axs[windgroup].axvline(plume_range_this[0])
            axs[windgroup].axvline(plume_range_this[1])
            meannumbers = windgroup_numbers.mean(axis=1)
            meantotalnumber = meannumbers.loc[plume_range_this[0]:plume_range_this[1]].mean()
            nr_peaks_15_min_after = (flights.loc[windgroup_numbers.columns.values.astype(int)].peaks_15_min_after == 1).sum()
            nr_no_peaks_15_min_after = (flights.loc[windgroup_numbers.columns.values.astype(int)].peaks_15_min_after == 0).sum()
            i=pd.Series({0:0,1:0,2:0})
            for head,oneflight in windgroup_numbers.items():
                flight_this = flights.loc[int(head)]
                flight_this_time_of_day = (flight_this.min_dist_time.hour + flight_this.min_dist_time.minute/60)
                if (flight_this.peaks_15_min_after == 1):
                    if i.iloc[1] == 0:
                        axs[windgroup].plot(oneflight.index,oneflight,c = "g",linewidth = 0.3,alpha = 0.5,label="number single flights with number peak after 15 min")
                        i.iloc[1] = 1
                    else: axs[windgroup].plot(oneflight.index,oneflight,c = "g",linewidth = 0.3,alpha = 0.5)
                else:
                    if i.iloc[0] == 0:
                        axs[windgroup].plot(oneflight.index,oneflight,c = "r",linewidth = 0.3,alpha = 0.5, label = "number single flights without number peak after 15 min")
                        i.iloc[0] = 1
                    else:  axs[windgroup].plot(oneflight.index,oneflight,c = "r",linewidth = 0.3,alpha = 0.5)

                # for (key,time_day_group),color in zip(time_day_groups.items(),['turquoise','darkblue','crimson']):
                #     if (time_day_group[0] < flight_this_time_of_day ) & (time_day_group[1] > flight_this_time_of_day ):
                #         print(time_day_group,key)
                #         if i.loc[key] == 0:
                #             axs[windgroup].semilogy(oneflight.index, oneflight, linewidth=0.3, alpha=0.8, color=color, label=f"number single flights between {time_day_group}h")
                #             i.loc[key] = 1
                #         else:
                #             axs[windgroup].plot(oneflight.index, oneflight, linewidth=0.3, alpha=0.5, color=color)




                min_dist_time_this = flight_this.min_dist_time
                otherflights_in_range = flights[(min_dist_time_this - pd.Timedelta(minutes = 10) < flights.min_dist_time)&(min_dist_time_this + pd.Timedelta(minutes = 40) > flights.min_dist_time)&(min_dist_time_this!= flights.min_dist_time)]
                # labels = ["overflight arr", "overflights dep", "no overflight arr", "no overflight dep"]
                # for group, label, color, linestyle in zip([1, 2, 3, 4], labels,
                #                                           ["C1", "C2", "C1", "C2" ],
                #                                           ["-", "-", "--", "--"]):
                #     print(group,label,color,linestyle)
                #     flights_this_group = otherflights_in_range[otherflights_in_range.overflight_group == group]
                #     if flights_this_group.size > 0:
                #         plt.vlines((flights_this_group["min_dist_time"] - min_dist_time_this).dt.total_seconds(), 10000 * group,
                #                   10000 * group + 10000, colors=color, linestyle=linestyle, linewidth=2,
                #                   label=f"group {group}: {label}", zorder=100)
                reftimes_other_flights = (otherflights_in_range.min_dist_time-min_dist_time_this).dt.total_seconds()
                axs[windgroup].vlines(reftimes_other_flights,1000,100000,colors="k",linewidth = 0.3,alpha = 0.5)
            axs[windgroup].plot(all_seconds,windgroup_numbers.mean(axis=1),label=f"number mean all")
            twinx = axs[windgroup].twinx()
            twinx.plot(all_seconds,windgroup_diameters.mean(axis=1),c="C1",label="diameter mean all")
            axs[windgroup].legend(loc=2)
            twinx.legend(loc=1)
            axs[windgroup].set_ylim(5000,100000)
            axs[windgroup].set_title(f"{label}, nr of flights {windgroup_diameters.shape[1]}(peak/nopeak) = ({nr_peaks_15_min_after}/{nr_no_peaks_15_min_after}), total mean in given range: {round(meantotalnumber)}, peak height {round(meannumbers.max())}")
            dates_str = f"{params.selected_dates[0]} - {params.selected_dates[-1]}"
    fig.suptitle(f"{dates_str}\nMean partector data of all flights of overflight group {select_overflight_group}, airplane group {select_plane_group}&{select_plane_group_2}")
    # ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    # fig.suptitle(f"{params.selected_dates}")
    # for windgroup in [0,1,2]:
    #     axs[windgroup].semilogy(all_overflights_windgroups[windgroup]["number"].index,all_overflights_data["number"].mean(axis = 1),label=f"over 0 plane 0 wind {windgroup}")
    #     # axs[3].plot(all_overflights_windgroups[windgroup]["diameter"].index,all_overflights_data["diameter"].mean(axis = 1),c="C1")
    #     axs[windgroup].axvline(0,c="k")
    # ax2.axvline(60*30,c="k")

    plt.show()

#   simpler plot

windgroup = 0
fig, ax = plt.subplots(3)
for windgroup in [0,1,2]:

    mask_plane = (
                flights.airplane_group_1_fanover50ps_2fanunder50ps_3propeller == select_plane_group)  # |(flights.airplane_group == select_plane_group_2)
    mask_overflight = (flights.overflight_group == select_overflight_group)
    mask_wind = (flights.Wind_group == windgroup)
    mask = mask_plane & mask_wind & mask_overflight & mask_no_flights_after
    mask_indices = mask[mask].index.astype(str)
    windgroup_numbers = numbers.loc[:, mask_indices]
    windgroup_diameters = diameters.loc[:, mask_indices]
    meannumbers = windgroup_numbers.mean(axis=1)


    for head, oneflight in windgroup_numbers.items():
        flight_this = flights.loc[int(head)]
        ax[windgroup].plot(oneflight.index, oneflight, c="gray", linewidth=0.3, alpha=0.5)

    ax[windgroup].plot(all_seconds,meannumbers)
    # twax = ax[windgroup].twinx()
    # twax.plot(all_seconds, windgroup_diameters.mean(axis=1),c="C1")
    # twax.set_ylim([10,70])
    ax[windgroup].axvline(0,c="C3")
    if windgroup == 1:
        ax[windgroup].set_ylabel("Particle number concentration [1/cm^3]")
        # twax.set_ylabel("Average particle diameter [nm]")
    if windgroup == 2:
        ax[windgroup].set_xlabel("Seconds since overflight arrival [s]")

    ax[windgroup].set_yscale("log")
    ax[windgroup].set_ylim([5000,1700000])
    ax[windgroup].set_xlim([-200,1200])

    # twax.plot(0,0,c="C1",label = "mean particle diameter")
    ax[windgroup].plot(0,0,c="C0",label = "mean number concentration")
    ax[windgroup].plot(0,0, c="gray", linewidth=0.5, label= "number concentration during each overflight")
    if windgroup == 0:
        ax[windgroup].legend(bbox_to_anchor=(0, 1.4), loc='upper left')
        # twax.legend(bbox_to_anchor=(1, 1.4), loc='upper right')
plt.show()