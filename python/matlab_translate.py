import datetime
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import lfilter


from readGPS import readGPS

def find_indices(el, az, emin, emax, azim1, azim2):
    """
    Find indices where elevation and azimuth angles fall within specified ranges.

    :param el: List of elevation angles
    :param az: List of azimuth angles
    :param emin: Minimum elevation angle
    :param emax: Maximum elevation angle
    :param azim1: Minimum azimuth angle
    :param azim2: Maximum azimuth angle
    :return: Array of indices satisfying the conditions
    """
    condition = (el > emin) & (el < emax) & \
                (az > azim1) & (az < azim2) & \
                (~np.isnan(az)) & (~np.isnan(el))

    indices = np.where(condition)[0]
    if indices.size > 0 and np.max(indices) >= el.size:
        az_trnaspose = az.T.flatten()
        condition_transposed = (el > emin) & (el < emax) & \
                               (az_trnaspose > azim1) & (az_trnaspose < azim2)
        indices = np.where(condition_transposed)[0]

    return indices

def smooth(data):
    """
    Simple moving average smoothing with a window size of 5. Translation matlab's smooth function.
    :param data: 1D array of data to be smoothed
    :return: data array of smoothed data
    """
    kernel = np.ones(5) / 5
    return np.convolve(data, kernel, mode='valid')


def get_ofac_hifac(elevAngles, cf, maxH, desiredPrec):
    """
    Calculate oversampling factor (ofac) and high-frequency factor (hifac) for Lomb-Scargle periodogram.
    Taken from gnssrefl library by Kristine M. Larson.

    :param elevAngles: array of elevation angles in degrees
    :param cf: carrier frequency in meters
    :param maxH: maximum reflector height in meters
    :param desiredPrec: desired precision in meters
    :return: (ofac, hifac)
    """
    X = np.sin(elevAngles * np.pi / 180) / cf

    # number of observations
    N = len(X)
    # observing Window length (or span)
    # units of inverse meters
    W = np.max(X) - np.min(X)
    if W == 0:
        print('bad window length - which will lead to illegal ofac/hifac calc')
        return 0, 0

    # characteristic peak width, meters
    cpw = 1 / W

    # oversampling factor
    ofac = cpw / desiredPrec

    # Nyquist frequency if the N observed data samples were evenly spaced
    # over the observing window span W, in meters
    fc = N / (2 * W)

    # Finally, the high-frequency factor is defined relative to fc
    hifac = maxH / fc

    return ofac, hifac

def peak2noise(f, p, frange):
    """
    Identifies the peak in power/amplitude array and computes peak-to-noise ratio.

    :param f: 1D array ox x-axis values.
    :param p: 1D array of power/amplitude values (same length as f).
    :param frange: 2-tuple/list (low, high) defining the range for noise estimation.
    :return: (maxRH, maxRHAmp, pknoise)
             maxRH: x-value at the maximum of p
             maxRHAmp: maximum value of p
             pknoise: maxRHAmp / mean(p in frange)
    """
    f = np.asarray(f)
    p = np.asarray(p)

    if f.shape != p.shape:
        raise ValueError("f and p must have the same shape")

    ij = int(np.argmax(p))
    maxRHAmp = float(p[ij])
    maxRH = float(f[ij])

    mask = np.where((f > frange[0]) | (f < frange[1]))[0]

    noisey = float(np.mean(p[mask]))
    pknoise = maxRHAmp / noisey
    return maxRH, maxRHAmp, pknoise

def lomb(t, h, ofac, hifac):
    """
    Computes the Lomb normalized periodogram of unevenly sampled data.
    Translated from Dmitry Savransky's original implementation in Matlab.

    :param t: 1D array of sample times (not necessarily evenly spaced)
    :param h: 1D array of data values (same length as t)
    :param ofac: oversampling factor (typically >= 4)
    :param hifac: high-frequency factor (multiple of average Nyquist frequency)
    :return: (f, P, prob, conf95)
             f: array of frequencies considered
             P: spectral amplitude at each frequency
             prob: false alarm probability (significance of power values)
             conf95: 95% confidence level amplitude
    """

    if t.shape != h.shape:
        raise ValueError("t and h must have the same shape")

    # Sample length and time span
    N = len(h)
    T = np.max(t) - np.min(t)

    # Mean and variance
    mu = np.mean(h)
    s2 = np.var(h, ddof=0)

    # Calculate sampling frequencies
    f_step = 1 / (T * ofac)
    f_max = hifac * N / (2 * T)
    f = np.arange(f_step, f_max + f_step, f_step)

    # Angular frequencies
    w = 2 * np.pi * f

    # Constant offsets (tau)
    sin_term = np.sum(np.sin(2 * w[:, np.newaxis] * t), axis=1)
    cos_term = np.sum(np.cos(2 * w[:, np.newaxis] * t), axis=1)
    tau = np.arctan2(sin_term, cos_term) / (2 * w)

    # Spectral power terms
    phase_shift = w[:, np.newaxis] * t - (w * tau)[:, np.newaxis]
    cterm = np.cos(phase_shift)
    sterm = np.sin(phase_shift)

    # Compute power
    h_centered = h - mu
    c_weighted = np.sum(cterm * h_centered, axis=1)
    s_weighted = np.sum(sterm * h_centered, axis=1)
    c_sum_sq = np.sum(cterm**2, axis=1)
    s_sum_sq = np.sum(sterm**2, axis=1)

    P = (c_weighted**2 / c_sum_sq + s_weighted**2 / s_sum_sq) / (2 * s2)

    # Estimate number of independent frequencies
    M = 2 * len(f) / ofac

    # Statistical significance (false alarm probability)
    prob = M * np.exp(-P)
    inds = prob > 0.01
    prob[inds] = 1 - (1 - np.exp(-P[inds]))**M

    # Convert power to amplitude
    P = 2 * np.sqrt(s2 * P / N)

    # 95% confidence level amplitude
    cf = 0.95
    conf95_power = -np.log(1 - (1 - (1 - cf))**(1 / M))
    conf95 = 2 * np.sqrt(s2 * conf95_power / N)

    return f, P, prob, conf95

def gps_to_nz(date_value, gps_seconds):
    base_date = datetime.strptime(str(int(date_value)), "%Y%m%d")
    gps_datetime = base_date + timedelta(seconds=float(gps_seconds))
    utc_datetime = gps_datetime - timedelta(seconds=18)
    return utc_datetime.replace(tzinfo=ZoneInfo("Pacific/Auckland"))

pvf = 2 # polynomial order used to remove the direct signal.
# this can be smaller, especially for short eleveation angle ranges.

min_rh = 0.4 # meters
minAmp = 2

min_points = 50

max_az_diff = 8

maxH = 8
desiredPrecision = 0.005

pcrit = 3.5

emin = 6
emax = 30

ediff = 8

cf = 0.1902936

az_range = 45
naz = round(360/az_range)

sampling_interval = 1 # need to get this from the data
av_time = 60 # smoothing time in seconds

coeff_ma = np.ones((1, int(av_time/sampling_interval))) * sampling_interval/av_time

snr_thresh = 36

# TODO: implement for loop, testing is fine to just do this once

azim1 = 0
azim2 = 360

max_diff_time = 30 # max jump in time/dropped data
files_path = Path("../data").rglob("2505*.LOG")
files_path = sorted(files_path, key=lambda x: x.name)

fig, ax = plt.subplots(2, 2, figsize=(10,10))
ax0 = ax[0,0]
ax90 = ax[0,1]
ax180 = ax[1,0]
ax270 = ax[1,1]

fig_retrieval, (ax_height, ax_peak) = plt.subplots(2,1, figsize=(8,6))
reflector_heights = []
peak_amplitudes = []
azimuths = []
datetime_list = []
for file in files_path:
    print("Parsing file:", file.name)
    gnss_data = readGPS(file, True)

    for prn, group in enumerate(gnss_data, start=1):
        if group.size == 0:
            continue

        #     get contiguous segments for prn
        elevation = group['el']
        azimuth = group['az']
        snr = group['snr']

        i = np.where((elevation > emin) & (elevation < emax) & (~np.isnan(snr)) & (~np.isnan(elevation)) & (~np.isnan(azimuth)))[0]
        idx = np.where((azimuth[i]>azim1) & (azimuth[i]<azim2))[0]
        i = i[idx]


        if len(i) > min_points:
            if (np.max(elevation[i]) - np.min(elevation[i]) > ediff
                and np.max(azimuth[i]) - np.min(azimuth[i]) < max_az_diff):
                print("found a valid track")
                minAmp, frange = 18, (6,2) # quicky_QC just returns these values, will move to function later
                pknoiseCrit = minAmp/2
                snr_subset = snr[i]
                snr_filter = lfilter(coeff_ma[0], 1, snr_subset)
                snr_index = np.where(snr_filter > snr_thresh)[0]
                if snr_index.size == 0:
                    continue
                snr_data = snr_subset[snr_index]
                elevation_angles = elevation[i][snr_index]
                azm = np.mean(azimuth[i])

                # convert from dB to linear
                snr_db = 10**(snr_data / 20)

                # Detrend the data
                p = np.polyfit(elevation_angles, snr_db, pvf)
                pv = np.polyval(p, elevation_angles)

                smooth_data = smooth(snr_db-pv).conj().T

                save_snr_idx = round(len(coeff_ma)/2)
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

                ofac, hifac = get_ofac_hifac(elevation_angles, cf/2, maxH, desiredPrecision)
                freq, power, prob, conf95 = lomb(sorted_x / (cf/2), sorted_y, ofac, hifac)
                maxRh, maxAmp, pknoise = peak2noise(freq, power, frange)
                maxObsElev = np.max(elevation_angles)
                minObsElev = np.min(elevation_angles)

                if (maxAmp > minAmp
                    and maxRh > min_rh
                    and pknoise > pcrit
                    and (maxObsElev - minObsElev) > ediff):

                    power_max = np.argmax(power)
                    idx = i[snr_index[j[power_max]]]
                    utc = group['utc'][idx]
                    date = group['date'][idx]

                    reflector_heights.append(maxRh)
                    peak_amplitudes.append(maxAmp)
                    azimuths.append(group['az'][idx])
                    print(date)
                    datetime_list.append(gps_to_nz(date, utc))

                    if 0 <= azm < 90:
                        ax0.plot(freq, power)
                    elif 90 <= azm < 180:
                        ax90.plot(freq, power)
                    elif 180 <= azm < 270:
                        ax180.plot(freq, power)
                    elif 270 <= azm < 360:
                        ax270.plot(freq, power)

start_datetime = datetime.strptime(files_path[0].stem, '%y%m%d%H').strftime('%d %b %Y %H:%m')
end_datetime = datetime.strptime(files_path[-1].stem, '%y%m%d%H').replace(minute=59).strftime('%d %b %Y %H:%m')
fig.suptitle(f"Height Retrievals by Azimuth Sector for {start_datetime}\nto\n{end_datetime}")

ax0.set_title("Azimuth 0-90°")
ax0.set_xlabel("Reflector Height (m)")
ax0.grid(True)

ax90.set_title("Azimuth 90-180°")
ax90.set_xlabel("Reflector Height (m)")
ax90.grid(True)

ax180.set_title("Azimuth 180-270°")
ax180.set_xlabel("Reflector Height (m)")
ax180.grid(True)

ax270.set_title("Azimuth 270-360°")
ax270.set_xlabel("Reflector Height (m)")
ax270.grid(True)

# Plot retreival metrics
fig_retrieval.suptitle(f"Retrieval Metrics for {start_datetime}\nto\n{end_datetime}")

ax_height.scatter(azimuths, reflector_heights)
ax_height.set_xlabel("Azimuth (degrees)")
ax_height.set_ylabel("Reflector Height (m)")
ax_height.grid(True)

ax_peak.scatter(azimuths, peak_amplitudes)
ax_peak.set_xlabel("Azimuth (degrees)")
ax_peak.set_ylabel("Peak Amplitude")
ax_peak.grid(True)

# Plot height over time
daily_heights= defaultdict(list)
for dt, height in zip(datetime_list, reflector_heights):
    daily_heights[dt.date()].append(height)

daily_dates = []
daily_avg_heights = []
for day in sorted(daily_heights):
    daily_dates.append(datetime.combine(day, datetime.min.time()))
    daily_avg_heights.append(np.mean(daily_heights[day]))

fig_height_time, ax_height_time = plt.subplots(figsize=(8, 6))
ax_height_time.plot(datetime_list, reflector_heights, marker='s', mfc='white', mec='black', linestyle='None', label='Individual Retrievals')
ax_height_time.plot(daily_dates, daily_avg_heights, marker='s', mfc='blue', mec='black', linestyle='None', label='Average Daily Retrievals')
ax_height_time.legend()
ax_height_time.grid(True)
ax_height_time.set_xlabel("Time (NZ)")
ax_height_time.set_ylabel("Reflector Height (m)")
fig_height_time.suptitle(f"Reflector Height over Time for {start_datetime} to {end_datetime}")

# set date format on x-axis
ax_height_time.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
ax_height_time.xaxis.set_major_locator(mdates.DayLocator())

plt.show()