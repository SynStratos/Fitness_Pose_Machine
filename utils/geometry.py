import math
import numpy as np

from logger import log


def point_distance(point1, point2):
    """

    @param point1:
    @param point2:
    @return:
    """
    x1, y1 = point1
    x2, y2 = point2

    return np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


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


def create_angle(p1, p2, p3, decimal=2):
    """
    auxiliary method that finds the value of the angle given three points in 2D space
    @param p1: first point
    @param p2: second point
    @param p3: third point or a reference axis ["axis_x", "axis_y"]
    @return: returns the angle in degrees
    """
    flag = 'axis' in p3

    x2, y2 = p2

    if "axis_y" in p3:
        p3 = x2, 0
    elif "axis_x" in p3:
        p3 = 0, y2

    try:
        p12 = point_distance(p1, p2)
        p13 = point_distance(p1, p3) #np.sqrt((x1 - x3) ** 2 + (y1 - y3) ** 2)
        p23 = point_distance(p3, p2) #np.sqrt((x3 - x2) ** 2 + (y3 - y2) ** 2)

        a = np.arccos((p12 ** 2 + p23 ** 2 - p13 ** 2) / (2 * p12 * p23))

        if np.isnan(a):
            a = 0

        a_deg = math.degrees(a)  # *180/math.pi

    except:
        log.debug("Exception for angle")
        a_deg = 0
    finally:
        if flag:
            a_deg = np.abs(90 - a_deg) + 90

    return round(a_deg, decimal)
