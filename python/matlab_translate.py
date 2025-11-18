import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

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
    return np.convolve(data, kernel, mode='same')


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

    mask = (f > frange[0]) & (f < frange[1])
    if not np.any(mask):

        return maxRH, maxRHAmp, np.nan

    noisey = float(np.mean(p[mask]))
    pknoise = maxRHAmp / noisey if noisey != 0 else np.inf
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
    t = np.asarray(t)
    h = np.asarray(h)

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

def nmea_to_datetime(date_val, utc_val):
    if date_val in (None, 0) or np.isnan(utc_val):
        return None
    year = int(date_val // 10000)
    month = int((date_val % 10000) // 100)
    day = int(date_val % 100)
    utc_int = int(utc_val)
    hour = int(utc_int // 10000)
    minute = int((utc_int % 10000) // 100)
    second = int(utc_int % 100)
    frac = utc_val - utc_int
    microseconds = int(round(frac * 1_000_000))
    try:
        return datetime(year, month, day, hour, minute, second, microseconds)
    except ValueError:
        return None


def resolve_date(date_array, idx):
    date_val = int(date_array[idx])
    if date_val != 0:
        return date_val
    for back in range(idx - 1, -1, -1):
        candidate = int(date_array[back])
        if candidate != 0:
            return candidate
    for forward in range(idx + 1, len(date_array)):
        candidate = int(date_array[forward])
        if candidate != 0:
            return candidate
    return 0


pvf = 2 # polynomial order used to remove the direct signal.
# this can be smaller, especially for short eleveation angle ranges.

min_rh = 0.4 # meters
minAmp = 15

maxH = 8
desiredPrecision = 0.005

pcrit = 3.5

emin = 5
emax = 30

ediff = 10

cf = 0.1902936

az_range = 45
naz = round(360/az_range)

# TODO: implement for loop, testing is fine to just do this once

azim1 = 0
azim2 = 360

gnss_data = readGPS("../data/25maytest.log", True)

height_times = []
height_values = []

for prn, group in enumerate(gnss_data, start=1):
    if group.size == 0:
        continue
    el = group['el']
    az = group['az']
    snr = group['snr']

    i = find_indices(el, az, emin, emax, azim1, azim2)

    if i.size == 0:
        continue
    elev_angles = el[i]
    if np.max(elev_angles) - np.min(elev_angles)>ediff:
        snr_db = np.power(10, snr[i]/20)

        az_mean = np.mean(az[i])

        # Detrend the data
        p = np.polyfit(elev_angles, snr_db, pvf, rcond=None)
        pv = np.polyval(p, elev_angles)
        save_snr = smooth(snr_db-pv).conj().T

        elev_angles_rad = np.radians(elev_angles) # convert to radians as np does not have sind function
        sine_e = np.sin(elev_angles_rad)

        sorted_x, j = np.unique(sine_e.conj().T, return_index=True)
        es = np.sin(np.radians(0.01))
        Fs = 1/es
        sorted_y = save_snr[j]
        sorted_x_int = np.arange(np.min(sorted_x), np.max(sorted_x) + es, es)
        sorted_y_int = np.interp(sorted_x_int, sorted_x, sorted_y)
        ofac, hifac = get_ofac_hifac(elev_angles, cf/2, maxH, desiredPrecision)

        freq, power, prob, conf95 = lomb(sorted_x_int / (cf/2), sorted_y_int, ofac, hifac)
        maxRh, maxAmp, pknoise = peak2noise(freq, power, (0, 8))
        if maxAmp > minAmp and maxRh > min_rh and pknoise > pcrit and (max(elev_angles) - min(elev_angles)) > ediff:
            dominant_local_idx = int(np.argmax(np.abs(save_snr)))
            dominant_global_idx = i[dominant_local_idx]
            date_val = resolve_date(group['date'], dominant_global_idx)
            timestamp = None
            if date_val != 0:
                timestamp = nmea_to_datetime(date_val, group['utc'][dominant_global_idx])
            if timestamp is not None:
                height_times.append(timestamp)
                height_values.append(maxRh)

            plt.plot(freq, power)
        plt.xlim(0, 10)

plt.show()
valid_points = [(t, h) for t, h in zip(height_times, height_values) if t is not None]
if not valid_points:
    print('No valid reflector heights found for plotting.')
else:
    print(valid_points)
    valid_points.sort(key=lambda x: x[0])
    plot_times, plot_heights = zip(*valid_points)
    plt.figure()
    plt.plot(plot_times, plot_heights, marker='o')
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    plt.gcf().autofmt_xdate()
    plt.show()
