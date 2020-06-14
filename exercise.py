import json
from exceptions import *


class Exercise:
    """

    """
    def __init__(self, config, side):
        if side not in ['s_e', 's_w']: raise Exception("Unexpected 'side' value.")
        config = json.load(config)
        self.name = config["exercise_name"]
        self.angles = config["angles_names"]
        self.angles_index = config["angles_to_check"][side]
        self.push_pull = config["push_pull"]
        self.mins = config["mins"]
        self.maxs = config["maxs"]
        self.mids = config["mids"]
        self.angles_order = config["angles_order"]
        self.rep_timeout = config["repetition_timeout"]
        self.tot_timeout = config["total_timeout"]
        self.n_repetition = config["n_repetition"]

        self.n_angles = len(self.angles_index)

        self.states = [0]*self.n_angles
        self.outputs = [0]*self.n_angles
        self.timestamps = [0]*self.n_angles

    def __check_pull_frame(self, angle, index, time, _min, _max, mid_point, tolerance=5):
        angle = abs(180 - angle)
        _min = abs(180 - _min)
        _max = abs(180 - _max)
        mid_point = abs(180 - mid_point)

        self.__check_push_frame__(angle, index, time, _min, _max, mid_point, tolerance)

    def __check_push_frame__(self, angle, index, time, _min, _max, mid_point, tolerance=5):
        """

        """
        # state 'none'
        if self.states[index] == 0:

            if angle >= _min:
                self.states[index] = 1

        # state 'start'
        elif self.states[index] == 1:

            if angle < _min:
                self.states[index] = 0
            elif angle >= mid_point:
                self.states[index] = 2

        # state 'rep_going'
        elif self.states[index] == 2:
            # goes to 'top'
            if angle >= (_max - tolerance) and angle <= (_max + tolerance):
                self.states[index] = 3
            # goes back to 'min' without completing the repetition
            elif angle <= _min:
                self.timestamps[index] = time
                self.outputs[index] = 2  # set to bad repetition
                self.states[index] = 0
            # goes directly over the top value, maybe skipped frames
            elif angle > (_max + tolerance):
                self.timestamps[index] = time
                self.outputs[index] = 2
                self.states[index] = 4

        # state 'top'
        elif self.states[index] == 3:
            # goes back to 'min'
            if angle <= _min:
                self.timestamps[index] = time
                self.outputs[index] = 1  # repetition correctly completed
                self.states[index] = 0
            # goes over the top value
            elif angle > (_max + tolerance):
                self.timestamps[index] = time
                self.outputs[index] = 2  # bad repetition
                self.states[index] = 4

        # state 'over_top'
        elif self.states[index] == 4:
            # goes back to min
            if angle <= _min:
                self.states[index] = 0
