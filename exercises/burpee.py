from exercises.exercise import Exercise
from utils.angles import create_angle


class Burpee(Exercise):
    def __init__(self, config, side, fps):
        super().__init__(config, side, fps)

    def __check_hands__(self, hand_sx, hand_dx):
        sx_x, sx_y = hand_sx
        dx_x, dx_y = hand_dx

        #TODO: controlli su mani
        if (sx_x == dx_x) and (sx_y == dx_y):
            # ovviamente estremizzata per il concetto -> necessaria definire un'area
            return True
        return False

    def __check_on_the_ground__(self, foot, shoulder, range):
        foot_x, foot_y = foot
        shoulder_x, shoulder_y = shoulder

        angle_ground = create_angle(foot, shoulder, (foot_x, shoulder_y))

        #TODO controlla angolo con range di reference
        if range[0] <= angle_ground <= range[-1]:
            return True
        else:
            return False
