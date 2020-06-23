from exercises.exercise import Exercise
from utils.angles import create_angle, mid_joint

from logger import log

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

    # TODO: controlli su mani
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

# def _check_at_180_(angle, **kwargs):
#     # TODO: set more precise values
#     if 180 <= angle <= 165:
#         joints = kwargs['joints']
#


class Burpee(Exercise):
    def __init__(self, config, side, fps):
        super().__init__(config, side, fps)

        #TODO: va letto dal json? o comunque va impostato in modo preciso (da decidere)
        self.CHECKS = [
            None,
            None,
            _check_hands_,
            None,
            _check_on_the_ground_,
            None
        ]
