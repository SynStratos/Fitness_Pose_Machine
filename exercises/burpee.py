from exercises.exercise import Exercise
from utils.angles import create_angle

ex_config = "./config/burpee_config.json"


def _check_hands_(hand_sx, hand_dx):
    sx_x, sx_y = hand_sx
    dx_x, dx_y = hand_dx

    # TODO: controlli su mani
    if (sx_x == dx_x) and (sx_y == dx_y):
        # ovviamente estremizzata per il concetto -> necessaria definire un'area
        return True
    return False


def _check_on_the_ground_(foot, shoulder, range):
    foot_x, foot_y = foot
    shoulder_x, shoulder_y = shoulder

    angle_ground = create_angle(foot, shoulder, (foot_x, shoulder_y))

    # TODO controlla angolo con range di reference
    if range[0] <= angle_ground <= range[-1]:
        return True
    else:
        return False


def _check_at_180_(angle, **kwargs):
    # TODO: set more precise values
    if 180 <= angle <= 165:
        joints = kwargs['joints']



class Burpee(Exercise):
    def __init__(self, config, side, fps):
        super().__init__(config, side, fps)

        #TODO: va letto dal json? o comunque va impostato in modo preciso
        self.CHECKS = [
            None,
            None,
            _check_hands_,
            None,
            _check_on_the_ground_,
            None
        ]
