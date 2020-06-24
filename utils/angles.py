import numpy as np
from copy import copy
import math


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

    for e, i in enumerate(indexes):
        series[:,i] = remove_missing(series[:,i], inplace)
        series[:,i] = remove_outliers(series[:,i], mids[e], inplace)
    #
    # for i in range(series.shape[1]):
    #     series[:,i] = remove_missing(series[:,i], inplace)
    #     series[:,i] = remove_outliers(series[:,i], mids[i], inplace)

    if not inplace:
        return series


def create_angle(p1, p2, p3):
    """
    auxiliary method that finds the value of the angle given three points in 2D space
    @param p1: first point
    @param p2: second point
    @param p3: third point
    @return: returns the angle in degrees
    """
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3

    p12 = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    p13 = np.sqrt((x1 - x3) ** 2 + (y1 - y3) ** 2)
    p23 = np.sqrt((x3 - x2) ** 2 + (y3 - y2) ** 2)

    a = np.arccos((p12 ** 2 + p23 ** 2 - p13 ** 2) / (2 * p12 * p23))

    if np.isnan(a):
        a = 0

    a_deg = math.degrees(a)  # *180/math.pi

    # round to 2 decimal (more? less?)
    return round(a_deg, 2)


def mid_joint(i, joints):
    """
    given a list containing two joints, it calculates a new join between them
    @param i: set of two indexes
    @param joints: set of joints
    @return: returns the generated joint
    """
    if type(i) == list:
        if len(i) == 2:
            x1, y1 = joints[i[0]]
            x2, y2 = joints[i[1]]

            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            return (x, y)
        else:
            raise Exception("Mid joint for more than 2 points not implemented yet.")
    else:
        return joints[i]