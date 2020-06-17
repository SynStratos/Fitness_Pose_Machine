import numpy as np
from copy import copy
from scipy.signal import medfilt
import statistics as stats
import math


def remove_missing(series_in, inplace=False):
    if type(series_in) != list and type(series_in) != np.ndarray:
        raise Exception("'series' must be of type 'list' or 'numpy.ndarray'.")
    if not inplace:
        series = copy(series_in)
    else:
        series = series_in
    for i, angle in enumerate(series):
        # skip first 2 elements
        if i > 1:
            # manage missing value (by default missing angles were set to zero)
            if angle == 0 or angle is None:
                series[i] = min([180, abs(2 * series[i - 1] - series[i - 2])])

    if not inplace:
        return series


def remove_outliers(series_in, _mid=None, _median=None, inplace=False):

    # TODO: mid must be known
    if type(series_in) != list and type(series_in) != np.ndarray:
        raise Exception("'series' must be of type 'list' or 'numpy.ndarray'.")
    if not inplace:
        series = copy(series_in)
    else:
        series = series_in

    mid = _mid #stats.mean(series)

    for i, angle in enumerate(series[:-1]):
        # skip first element
        if i > 0:
            threshold = (series[i - 1] + series[i + 1]) / 2
            if (mid < angle < threshold) or (mid > angle > threshold):
                series[i] = threshold

    #TODO: how to do it without the full series
    """
    filtered = medfilt(series, _median)
    for i in range(len(series)):
        series[i] = filtered[i]
    """
    if not inplace:
        return series


def preprocess_angles(series_in, mids, inplace=False):
  if type(series_in) != np.ndarray:
    raise Exception("'series' must be of type numpy.ndarray'.")
  if not inplace:
    series = copy(series_in)
  else:
    series = series_in

  for i in range(series.shape[1]):
    series[:,i] = remove_missing(series[:,i], inplace)
    series[:,i] = remove_outliers(series[:,i], mids[i], inplace)

  if not inplace:
    return series


def create_angle(p1, p2, p3):
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    p12 = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    p13 = np.sqrt((x1 - x3) ** 2 + (y1 - y3) ** 2)
    p23 = np.sqrt((x3 - x2) ** 2 + (y3 - y2) ** 2)

    a = np.arccos((p12 ** 2 + p23 ** 2 - p13 ** 2) / (2 * p12 * p23))

    a_deg = math.degrees(a)  # *180/math.pi

    # round to 2 decimal (more? less?)
    return round(a_deg, 2)
