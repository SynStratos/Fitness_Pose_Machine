import numpy as np
from copy import copy
import pandas as pd

def remove_missing(series_in, inplace=False):
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
            if angle == 0 or angle is None:
                series[i] = round(min([180, abs(2 * series[i - 1] - series[i - 2])]), 2)

    if not inplace:
        return series


def remove_outliers(series_in, _mid=None, _median=None, inplace=False):
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
                series[i] = round(threshold, 2)

    #TODO: how to do it without the full series
    """
    filtered = medfilt(series, _median)
    for i in range(len(series)):
        series[i] = filtered[i]
    """
    if not inplace:
        return series


def preprocess_angles(series_in, indexes, mids, inplace=False):
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

    for e, i in enumerate(pd.Series(indexes).drop_duplicates().tolist()):
        series[:,i] = remove_missing(series[:,i], inplace)
        series[:,i] = remove_outliers(series[:,i], mids[e], inplace)
    #
    # for i in range(series.shape[1]):
    #     series[:,i] = remove_missing(series[:,i], inplace)
    #     series[:,i] = remove_outliers(series[:,i], mids[i], inplace)

    if not inplace:
        return series
