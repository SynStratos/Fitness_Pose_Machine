from exercises.exercise import Exercise
from utils.geometry import mid_joint, create_angle, point_distance

from logger import log

import numpy as np

ex_config = "./config/burpee_config.json"


def _shoulder_hand_distance_sx(joints):
    """
    calculates the distance of the left hand and should joints projected on the x axis
    @param joints:
    @return: distance between the two points or 99999 if any error occured (e.g. joint is missing)
    """
    try:
        hand_sx = joints[7]
        shoudler_sx = joints[5]
        log.debug("left hand-should distance: ", str(hand_sx[1] - shoudler_sx[1]))
        return hand_sx[1] - shoudler_sx[1]
    except:
        return 99999


def _shoulder_hand_distance_dx(joints):
    """
    calculates the distance of the right hand and should joints projected on the x axis
    @param joints:
    @return: distance between the two points or 99999 if any error occured (e.g. joint is missing)
    """
    try:
        hand_dx = joints[4]
        shoudler_dx = joints[2]
        log.debug("right hand-should distance: ", str(hand_dx[1] - shoudler_dx[1]))
        return hand_dx[1] - shoudler_dx[1]
    except:
        return 99999


def _check_hands(angle, **kwargs):
    joints = kwargs['joints']

    # TODO: fallo più bello
    try:
        hand_shoulder_sx = joints[7][1] < joints[5][1]
    except:
        hand_shoulder_sx = False

    try:
        hand_shoulder_dx = joints[4][1] < joints[2][1]
    except:
        hand_shoulder_dx = False

    try:
        distance = point_distance(joints[7], joints[4])
        log.debug("distance between hands: ", str(distance))
    except:
        distance = 99999

    # TODO: check if 20 is okay as threshold
    # check person is standing + hands are close + at least one hand is over the respective shoulder (this manages joints missing for one of the sides)
    return (79 <= angle <= 90) and (distance <= 24) and (hand_shoulder_dx or hand_shoulder_sx)


def test_check_floor(angle, **kwargs):
    threshold_chest_on_the_ground = 20
    return (0 <= angle <= 30) and \
           ((_shoulder_hand_distance_dx(kwargs['joints']) <= threshold_chest_on_the_ground and kwargs['side'] == "s_e")
            or
            (_shoulder_hand_distance_sx(kwargs['joints']) <= threshold_chest_on_the_ground and kwargs['side'] == "s_w"))
    # arriva anche a ~15 - 10
    # ((_shoulder_hand_distance_dx(kwargs['joints']) <= threshold_chest_on_the_ground )
    #  or
    #  (_shoulder_hand_distance_sx(kwargs['joints']) <= threshold_chest_on_the_ground ))


class Burpee(Exercise):
    def __init__(self, config, side, fps):
        config = ex_config
        super().__init__(config, side, fps)

        self.CHECKS = [
            None,
            _check_hands,
            test_check_floor
        ]