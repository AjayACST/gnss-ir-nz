from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

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

def gps_to_nz(date_value, gps_seconds):
    base_date = datetime.strptime(str(int(date_value)), "%Y%m%d")
    gps_datetime = base_date + timedelta(seconds=float(gps_seconds))
    utc_datetime = gps_datetime - timedelta(seconds=18)
    return utc_datetime.replace(tzinfo=ZoneInfo("Pacific/Auckland"))