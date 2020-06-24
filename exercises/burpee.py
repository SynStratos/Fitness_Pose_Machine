from exercises.exercise import Exercise
from utils.geometry import mid_joint, create_angle, point_distance

from logger import log

import numpy as np

ex_config = "./config/burpee_config.json"


def _check_hands_(angle, **kwargs):
    """
    specific check method for a burpee exercise that checks if the hands are close to them when the person is standing
    @param angle:
    @param kwargs:
    @return:
    """
    if 180 <= angle <= 165:
        return False

    # todo: add additional condition to check if the person is standing? ~90° head-hip-ground

    joints = kwargs['joints']

    # check if the person is standing
    neck = joints[1]
    feet_center = mid_joint([10, 13], joints)
    x_parallel = [0, feet_center[1]]

    vertical_angle = create_angle(neck, feet_center, x_parallel)

    # TODO: to be tuned
    if 90 <= vertical_angle <= 70:
        log.debug("Person is not standing.")
        return False

    # check if hands are close
    hand_sx = joints[7]
    hand_dx = joints[4]

    sx_x, sx_y = hand_sx
    dx_x, dx_y = hand_dx

    # TODO: controlli su mani - definire range di distanza
    if (sx_x == dx_x) and (sx_y == dx_y):
        # ovviamente estremizzata per il concetto -> necessaria definire un'area
        return True
    return False


def _check_on_the_ground_(angle, **kwargs):
    """
    specific check method for a burpee exercise that checks if person is ~parallel to the ground when lying
    @param angle:
    @param kwargs:
    @return:
    """
    if 180 <= angle <= 165:
        return False

    joints = kwargs['joints']

    try:
        orientation = kwargs['orientation']
    except Exception:
        raise Exception("Missing orientation argument.")

    if orientation == 's_e':
        # [ / ]
        foot, shoulder = joints[10], joints[2]
    elif orientation == 's_w':
        # [ \ ]
        foot, shoulder = joints[13], joints[5]
    else:
        raise Exception("Unespected value for orientation.")

    #TODO: definire i valori corretti di questo range
    range = [30, 60]

    foot_x, foot_y = foot
    shoulder_x, shoulder_y = shoulder

    if foot_y < shoulder_y:
        log.debug("Foot is lower than shoulder.")
        return False

    angle_ground = create_angle(foot, shoulder, (foot_x, shoulder_y))

    # TODO controlla angolo con range di reference
    if range[0] <= angle_ground <= range[-1]:
        log.debug("Person is lying on the floor.")
        return True
    else:
        return False


def standing_angle(joints):
    neck = joints[1]
    feet_center = mid_joint([10, 13], joints)
    x_parallel = [0, feet_center[1]]
    angle = create_angle(neck, feet_center, x_parallel)
    print("angle", angle)
    return np.abs(90 - angle) + 90


def test_check_true(angle, **kwargs):
    joints = kwargs['joints']
    print("Sono un controllo sull'angolo -  good!")
    return True


def test_check_false(angle, **kwargs):
    joints = kwargs['joints']
    print("Sono un controllo sull'angolo -  bad!")
    return False


def test_check_hands(angle, **kwargs):
    joints = kwargs['joints']

    try:
        distance = point_distance(joints[7], joints[4])
    except:
        distance = 99999
    print(distance)

    return (90 <= angle <= 105) and (distance <= 20)


class Burpee(Exercise):
    def __init__(self, config, side, fps):
        config = ex_config
        super().__init__(config, side, fps)

        self.CHECKS = [
            None,
            test_check_hands
        ]


    def process_frame(self, frame, exercise_over=False, **kwargs):

        # TODO: farlo direttamente al livello del calcolo degli angoli? -> così più facile ma boh

        # add angle needed only for burpee
        frame[-1] = np.abs(90 - frame[-1]) + 90
        # frame = np.concatenate([frame, [standing_angle(joints)]], axis=0)
        print(frame[-1])
        super().process_frame(frame, exercise_over=False, **kwargs)
