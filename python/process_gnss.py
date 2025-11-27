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
    def __init__(self, azimuth_bins, min_el=6, max_el=30):
        self.reflector_heights = []
        self.peak_amplitudes = []
        self.azimuths = []
        self.datetime_list = []
        self.freq_list = []
        self.power_list = []
        self.peak_noise = []

        self.pvf = config['gnssr_parameters'].getint('pvf') # polynomial order used to remove the direct signal.`
        self.min_rh = config['gnssr_parameters'].getfloat('min_rh') # meters
        self.min_points = config['gnssr_parameters'].getint('min_points')
        self.max_az_diff = config['gnssr_parameters'].getint('max_az_diff')
        self.max_height = config['gnssr_parameters'].getint('max_height')
        self.desired_precision = 0.005
        self.pcrit = config['gnssr_parameters'].getfloat('pcrit')
        self.emin = min_el
        self.emax = max_el
        self.ediff = config['gnssr_parameters'].getint('ediff')
        self.cf = config['gnssr_parameters'].getfloat('cf')
        self.snr_thresh = config['gnssr_parameters'].getint('snr_thresh')
        self.sampling_interval = config['gnssr_parameters'].getint('sampling_interval') # need to get this from the data
        self.av_time = config['gnssr_parameters'].getint('av_time')
        self.coeff_ma = np.ones((1, int(self.av_time/self.sampling_interval))) * self.sampling_interval/self.av_time

        self.azimuth_bins = azimuth_bins

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

            i = np.where(
                (elevation > self.emin) & (elevation < self.emax) & (~np.isnan(snr)) & (~np.isnan(elevation)) & (
                    ~np.isnan(azimuth)))[0]

            # create azimuth mask
            mask = np.zeros(i.shape, dtype=bool)
            for min_v, max_v in self.azimuth_bins:
                current_range_mask = (azimuth[i] > min_v) & (azimuth[i] < max_v)
                mask = np.logical_or(mask, current_range_mask)
            i = i[mask]

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
                        self.peak_noise.append(pknoise)

                        self.freq_list.append(freq)
                        self.power_list.append(power)

    def guard_graphs(self):
        """
        Ensure that there is data to graph before attempting to do so.
        :return: True if there is data to graph, False otherwise.
        """
        if len(self.reflector_heights) == 0:
            print("No reflector heights detected. Cannot generate graphs.")
            exit(1)

    def graph_azimuths(self, date: datetime.datetime):
        """
        Graph the azimuths of detected reflector heights, for a particular day, in groups of 90 degrees.
        :param date: Date corresponding to the GNSS data to be displayed.
        :return: None
        """
        self.guard_graphs()
        # check date is in date list
        if all(dt.date() != date.date() for dt in self.datetime_list):
            print("No data for the specified date: {}. Cannot generate graph.".format(date.strftime('%Y-%m-%d')))
            return
        start_date = date.strftime('%d %b %Y %H:%m')
        end_date = date.replace(minute=59).strftime('%d %b %Y %H:%m')
        fig, ax = plt.subplots(2, 2, figsize=(10,10))
        fig.suptitle("Height Retrievals by Azimuth Sector for {}\nto\n{}".format(start_date, end_date))
        for i in range(len(self.azimuth_bins)):
            start, end = self.azimuth_bins[i]
            ax_sector = ax[i//2, i%2]
            ax_sector.set_title("Azimuth {}-{}°".format(int(start), int(end)))
            ax_sector.set_xlabel("Reflector Height (m)")
            ax_sector.grid()

        for freq, power, az, dt in zip(self.freq_list, self.power_list, self.azimuths, self.datetime_list):
            if dt.date() == date.date():
                for i in range(len(self.azimuth_bins)):
                    start, end = self.azimuth_bins[i]
                    if start < az < end:
                        ax_sector = ax[i//2, i%2]
                        ax_sector.plot(freq, power)
        fig.show()

    def graph_retrieval_metrics(self, date: datetime.datetime):
        """
        Graph the retrieval metrics of detected reflector heights, for a particular day.
        :param date: Date corresponding to the GNSS data to be displayed.
        :return: None
        """
        self.guard_graphs()
        # check date is in date list
        if all(dt.date() != date.date() for dt in self.datetime_list):
            print("No data for the specified date: {}. Cannot generate graph.".format(date.strftime('%Y-%m-%d')))
            return
        start_date = date.strftime('%d %b %Y %H:%m')
        end_date = date.replace(minute=59).strftime('%d %b %Y %H:%m')
        fig_retrieval, (ax_height, ax_peak, ax_noise) = plt.subplots(3, 1, figsize=(8, 10))

        fig_retrieval.suptitle("Retrieval Metrics for {}\nto\n{}".format(start_date, end_date))

        ax_height.set_xlabel("Azimuth (degrees)")
        ax_height.set_ylabel("Reflector Height (m)")
        ax_height.set_ylim(self.min_rh, self.max_height)
        ax_height.grid()

        ax_peak.set_xlabel("Azimuth (degrees)")
        ax_peak.set_ylabel("Peak Amplitude")
        ax_peak.grid()

        ax_noise.set_xlabel("Azimuth (degrees)")
        ax_noise.set_ylabel("Peak to Noise Ratio")
        ax_noise.grid()

        for rh, pa, pk, az, dt in zip(self.reflector_heights, self.peak_amplitudes, self.peak_noise, self.azimuths, self.datetime_list):
            if dt.date() == date.date():
                ax_height.scatter(az, rh)
                ax_peak.scatter(az, pa)
                ax_noise.scatter(az, pk)

        ax_peak.plot()
        fig_retrieval.show()

    def graph_height_time(self):
        """
        Graph the reflector heights over time.
        :return: None
        """
        self.guard_graphs()
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
