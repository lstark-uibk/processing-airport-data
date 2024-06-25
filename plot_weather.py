import os.path
import datetime
import glob
import params
import readinflights
import readinpartector
import readinweather
import readinmicrophone
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import pytz
import h5py
from scipy.interpolate import interp1d
import datetime

weather = readinweather.read_in_data_of_muliple_days(os.path.join(params.parentdir, "weather"), params.selected_dates)
smoothing = 5
weather = weather.drop(columns = "Time").rolling(window=10).mean()
fig,axs = plt.subplots(3,1,sharex=True)
ax2 = {}
for i, line1,line2 in zip([0,1,2],["Temperature","Wind Dir","Solar radiation"],["Humidity","Wind Speed","Precip. Accum."]):
    axs[i].plot(weather.index,weather[line1],label= line1,c=f"C{2*i}")
    axs[i].legend(loc = 2)
    if line2:
        ax2[i] = axs[i].twinx()
        ax2[i].plot(weather.index,weather[line2],label= line2,c=f"C{2*i+1}")
        ax2[i].legend(loc=1)
    # axs[i].xaxis.set_major_locator(mdates.DayLocator())
    axs[i].xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%H'))
    axs[i].grid()

plt.show()
