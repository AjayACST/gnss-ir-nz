import numpy as np

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