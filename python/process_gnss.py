import configparser
import datetime
from collections import defaultdict

import numpy as np
from scipy.signal import lfilter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from utils import smooth, get_ofac_hifac, peak2noise, gps_to_nz
from lombscargle import lomb
config = configparser.ConfigParser()
config.read('config.ini')

class GNSSProcessor:
    def __init__(self):
        self.reflector_heights = []
        self.peak_amplitudes = []
        self.azimuths = []
        self.datetime_list = []
        self.freq_list = []
        self.power_list = []

        self.pvf = config['DEFAULT'].getint('pvf') # polynomial order used to remove the direct signal.`
        self.min_rh = config['DEFAULT'].getfloat('min_rh') # meters
        self.min_amp = config['DEFAULT'].getint('min_amp')
        self.min_points = config['DEFAULT'].getint('min_points')
        self.max_az_diff = config['DEFAULT'].getint('max_az_diff')
        self.max_height = config['DEFAULT'].getint('max_height')
        self.desired_precision = config['DEFAULT'].getfloat('desired_precision')
        self.pcrit = config['DEFAULT'].getfloat('pcrit')
        self.emin = config['DEFAULT'].getint('emin')
        self.emax = config['DEFAULT'].getint('emax')
        self.ediff = config['DEFAULT'].getint('ediff')
        self.cf = config['DEFAULT'].getfloat('cf')
        self.snr_thresh = config['DEFAULT'].getint('snr_thresh')
        self.sampling_interval = config['DEFAULT'].getint('sampling_interval') # need to get this from the data
        self.av_time = config['DEFAULT'].getint('av_time')
        self.coeff_ma = np.ones((1, int(self.av_time/self.sampling_interval))) * self.sampling_interval/self.av_time

        self.azim1 = config['DEFAULT'].getint('azim1')
        self.azim2 = config['DEFAULT'].getint('azim2')

    def process_gnss(self, gnss_data):
        """
        Process GNSS data to extract reflector heights and related information. Frequency and power spectra are computed
        using Lomb-Scargle periodogram. The results are stored in the class attributes.

        :param gnss_data: The data read from `readGPS` function, structured as a list of numpy arrays for each PRN.
        :return: None
        """
        for prn, group in enumerate(gnss_data, start=1):
            if group.size == 0:
                continue

            elevation = group['el']
            azimuth = group['az']
            snr = group['snr']

            i = np.where((elevation > self.emin) & (elevation < self.emax) & (~np.isnan(snr)) & (~np.isnan(elevation)) & (~np.isnan(azimuth)))[0]
            idx = np.where((azimuth[i]>self.azim1) & (azimuth[i]<self.azim2))[0]
            i = i[idx]

            if len(i) > self.min_points:
                if (np.max(elevation[i]) - np.min(elevation[i]) > self.ediff
                    and np.max(azimuth[i]) - np.min(azimuth[i]) < self.max_az_diff):
                    minAmp, frange = 18, (6,2)
                    snr_subset = snr[i]
                    snr_filter = lfilter(self.coeff_ma[0], 1, snr_subset)
                    snr_index = np.where(snr_filter > self.snr_thresh)[0]
                    if snr_index.size == 0:
                        continue
                    snr_data = snr_subset[snr_index]
                    elevation_angles = elevation[i][snr_index]
                    azm = np.mean(azimuth[i])

                    # convert from dB to linear
                    snr_db = 10**(snr_data / 20)

                    # Detrend the data
                    p = np.polyfit(elevation_angles, snr_db, self.pvf)
                    pv = np.polyval(p, elevation_angles)

                    smooth_data = smooth(snr_db-pv).conj().T

                    save_snr_idx = round(len(self.coeff_ma)/2)
                    if len(smooth_data) <= save_snr_idx:
                        continue
                    save_snr = smooth_data[save_snr_idx:]
                    # fft is done on the sine of the elevation angles
                    aligned_elev = elevation_angles[save_snr_idx:]
                    trim_len = min(len(save_snr), len(aligned_elev))
                    if trim_len == 0:
                        continue
                    save_snr = save_snr[:trim_len]
                    aligned_elev = aligned_elev[:trim_len]
                    elev_angels = np.radians(aligned_elev) # convert to radians as np does not have sind function
                    sine_e = np.sin(elev_angels)

                    # sort the data so all tracks are rising
                    sorted_x, j = np.unique(sine_e.conj().T, return_index=True)

                    sorted_y = save_snr[j]
                    sorted_x = sorted_x[1:-1]
                    sorted_y = sorted_y[1:-1]

                    ofac, hifac = get_ofac_hifac(elevation_angles, self.cf/2, self.max_height, self.desired_precision)
                    freq, power, prob, conf95 = lomb(sorted_x / (self.cf/2), sorted_y, ofac, hifac)
                    maxRh, maxAmp, pknoise = peak2noise(freq, power, frange)
                    maxObsElev = np.max(elevation_angles)
                    minObsElev = np.min(elevation_angles)

                    if (maxAmp > minAmp
                        and maxRh > self.min_rh
                        and pknoise > self.pcrit
                        and (maxObsElev - minObsElev) > self.ediff):

                        power_max = np.argmax(power)
                        idx = i[snr_index[j[power_max]]]
                        utc = group['utc'][idx]
                        date = group['date'][idx]

                        self.reflector_heights.append(maxRh)
                        self.peak_amplitudes.append(maxAmp)
                        self.azimuths.append(group['az'][idx])
                        self.datetime_list.append(gps_to_nz(date, utc))

                        self.freq_list.append(freq)
                        self.power_list.append(power)

    def graph_azimuths(self, date: datetime.datetime):
        """
        Graph the azimuths of detected reflector heights, for a particular day, in groups of 90 degrees.
        :param date: Date corresponding to the GNSS data to be displayed.
        :return: None
        """
        start_date = date.strftime('%d %b %Y %H:%m')
        end_date = date.replace(minute=59).strftime('%d %b %Y %H:%m')
        fig, ax = plt.subplots(2, 2, figsize=(10,10))
        fig.suptitle("Height Retrievals by Azimuth Sector for {}\nto\n{}".format(start_date, end_date))
        ax0 = ax[0,0]
        ax0.set_title("Azimuth 0-90°")
        ax0.set_xlabel("Reflector Height (m)")
        ax0.grid()

        ax90 = ax[0,1]
        ax90.set_title("Azimuth 90-180°")
        ax90.set_xlabel("Reflector Height (m)")
        ax90.grid()

        ax180 = ax[1,0]
        ax180.set_title("Azimuth 180-270°")
        ax180.set_xlabel("Reflector Height (m)")
        ax180.grid()

        ax270 = ax[1,1]
        ax270.set_title("Azimuth 270-360°")
        ax270.set_xlabel("Reflector Height (m)")
        ax270.grid()

        for freq, power, az, dt in zip(self.freq_list, self.power_list, self.azimuths, self.datetime_list):
            if dt.date() == date.date():
                if 0 <= az < 90:
                    ax0.plot(freq, power)
                elif 90 <= az < 180:
                    ax90.plot(freq, power)
                elif 180 <= az < 270:
                    ax180.plot(freq, power)
                elif 270 <= az < 360:
                    ax270.plot(freq, power)
        fig.show()

    def graph_retrieval_metrics(self, date: datetime.datetime):
        """
        Graph the retrieval metrics of detected reflector heights, for a particular day.
        :param date: Date corresponding to the GNSS data to be displayed.
        :return: None
        """
        start_date = date.strftime('%d %b %Y %H:%m')
        end_date = date.replace(minute=59).strftime('%d %b %Y %H:%m')
        fig_retrieval, (ax_height, ax_peak) = plt.subplots(2, 1, figsize=(8, 10))

        fig_retrieval.suptitle("Retrieval Metrics for {}\nto\n{}".format(start_date, end_date))

        ax_height.set_xlabel("Azimuth (degrees)")
        ax_height.set_ylabel("Reflector Height (m)")
        ax_height.grid()

        ax_peak.set_xlabel("Azimuth (degrees)")
        ax_peak.set_ylabel("Peak Amplitude")
        ax_peak.grid()

        for rh, pa, az, dt in zip(self.reflector_heights, self.peak_amplitudes, self.azimuths, self.datetime_list):
            if dt.date() == date.date():
                ax_height.scatter(az, rh)
                ax_peak.scatter(az, pa)
        fig_retrieval.show()

    def graph_height_time(self):
        """
        Graph the reflector heights over time.
        :return: None
        """
        start_date = self.datetime_list[0].strftime('%d %b %Y %H:%m')
        end_date = self.datetime_list[-1].strftime('%d %b %Y %H:%m')
        daily_heights= defaultdict(list)
        for dt, height in zip(self.datetime_list, self.reflector_heights):
            daily_heights[dt.date()].append(height)

        daily_dates = []
        daily_avg_heights = []
        for day in sorted(daily_heights):
            daily_dates.append(datetime.datetime.combine(day, datetime.datetime.min.time()))
            daily_avg_heights.append(np.mean(daily_heights[day]))

        fig_height_time, ax_height_time = plt.subplots(figsize=(8, 6))
        ax_height_time.plot(self.datetime_list, self.reflector_heights, marker='s', mfc='white', mec='black', linestyle='None', label='Individual Retrievals')
        ax_height_time.plot(daily_dates, daily_avg_heights, marker='s', mfc='blue', mec='black', linestyle='None', label='Average Daily Retrievals')
        ax_height_time.legend()
        ax_height_time.grid()
        ax_height_time.set_xlabel("Time (NZ)")
        ax_height_time.set_ylabel("Reflector Height (m)")
        fig_height_time.suptitle("Reflector Height over Time for {}\nto\n{}".format(start_date, end_date))

        ax_height_time.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
        ax_height_time.xaxis.set_major_locator(mdates.DayLocator())

        fig_height_time.show()
