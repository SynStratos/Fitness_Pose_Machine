import pandas as pd
import numpy as np
from copy import copy

from logger import log


def remove_missing(series_in, cap_value, inplace=False):
    """
    method that removes missing values from a set of angles
    @param series_in: starting set of angles
    @param inplace: apply modification on the starting array if True, else it creates a new array
    @return: returns the filled set of angles if not inplace
    """
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
            if angle is None:
                log.debug("Remove missing angle.")
                series[i] = round(min([cap_value, max(0, 2 * series[i - 1] - series[i - 2])]), 2)

    if not inplace:
        return series


def remove_noise(series_in, _mid=None, _median=None, inplace=False):
    """
    method that remove outliers from a set of angles
    @param series_in: starting set of angles
    @param _mid:
    @param _median:
    @param inplace: apply modification on the starting array if True, else it creates a new array
    @return: returns the cleaned set of angles if not inplace
    """
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
                log.debug("Removing noise from signal.")
                series[i] = round(threshold, 2)

    #TODO: how to do it without the full series
    """
    filtered = medfilt(series, _median)
    for i in range(len(series)):
        series[i] = filtered[i]
    """
    if not inplace:
        return series


def remove_outlier(series_in, _mid=None, _median=None, inplace=False):
    """

    @param series_in:
    @param _mid:
    @param _median:
    @param inplace:
    @return:
    """
    if type(series_in) != list and type(series_in) != np.ndarray:
        raise Exception("'series' must be of type 'list' or 'numpy.ndarray'.")
    if not inplace:
        series = copy(series_in)
    else:
        series = series_in
    for i, angle in enumerate(series[:-1]):
        # skip first 2 elements
        if i > 0:
            log.debug("Removing outlier value for angle.")
            # manage missing value (by default missing angles were set to zero)
            series[i] = (series[i - 1] + series[i + 1]) / 2

    if not inplace:
        return series


def preprocess_angles(series_in, indexes, mids, cap_values=None, inplace=False):
    """
    methods that applies different preprocessing methods to a set of angles
    @param series_in: starting set of angles
    @param mids:
    @param inplace: apply modification on the starting array if True, else it creates a new array
    @return: returns the cleaned set of angles if not inplace
    """
    if type(series_in) != np.ndarray:
        raise Exception("'series' must be of type numpy.ndarray'.")
    if not inplace:
        series = copy(series_in)
    else:
        series = series_in

    if not cap_values:
        # if no cap values are provided, all the values are set to 180 by default
        cap_values = [180]*len(series_in)

    if len(cap_values) != len(series_in):
        raise Exception("Provided 'cap_values' array must have the same lenght of the number of angles contained in 'series_in'.")

    for e, i in enumerate(pd.Series(indexes).drop_duplicates().tolist()):
        series[:, i] = remove_missing(series[:, i], cap_values[i], inplace)
        #series[:, i] = remove_outlier(series[:, i], mids[e], inplace)
        series[:, i] = remove_noise(series[:, i], mids[e], inplace)

    if not inplace:
        return series