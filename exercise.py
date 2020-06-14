import json
from exceptions import *

from logger import log
from utils.angles import preprocess_angles

STATES = [
         'none',
         'start',
         'rep_going',
         'top',
         'over_top'
]

OUTPUTS = [
          'no_rep',
          'rep_ok',
          'rep_bad'
          ]


class Exercise:
    """

    """
    def __init__(self, config, side, fps):
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

        self.fps = fps

        self.time = 0
        self.states = [0]*self.n_angles
        self.outputs = [0]*self.n_angles
        self.timestamps = [0]*self.n_angles
        self.n_timeout = int(self.tot_timeout / self.rep_timeout)
        self.countdown = int(fps * self.rep_timeout)
        self.timed_out = False

        self.num_good_reps = 0
        self.num_bad_reps = 0
        self.time_out_series = 0

    def __check_pull_frame__(self, angle, index, time, _min, _max, mid_point, tolerance=5):
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

    def __check_order__(self):
        """
        return: True se ordine corretto, False se ordine errato
        """
        if not self.angles_order:
            return True
        elif len(self.angles_order) < 2:
            raise Exception("cant check order of a single element")

        for i, o in enumerate(self.angles_order):
            for angle_x in o:
                for oo in self.angles_order[i + 1:]:
                    for angle_y in oo:
                        if (self.timestamps[angle_x] >= self.timestamps[angle_y]) and (self.timestamps[angle_x] > 0) and (self.timestamps[angle_y] > 0):
                            print("Wrong order: you moved your {} before your {}.".format(self.angles[angle_x], self.angles[angle_y]))
                            return False

        return True

    def __check_repetition__(self):
        if len(set(self.outputs)) == 1 and self.outputs[0] == 1:
            return self.__check_order__()
        else:
            if len(set(self.outputs)) == 1 and self.outputs[0] == 2:
                print("All movements where wrong!")
            else:
                for i, o in enumerate(self.outputs):
                    print("Movement for {} was {}!".format(self.angles[i], OUTPUTS[o]))
            return False

    def process_frame(self, ):
        repetition_ended = False
        for i in range(len(self.angles)):
            if self.push_pull[i] == "push":
                self.__check_push_frame__()
            elif self.push_pull[i] == "pull":
                self.__check_pull_frame__()

            if self.outputs[i] in [1, 2] and self.states[0] == 1:
                repetition_ended = True
        self.time += 1

        if self.countdown == 0:
            self.time_out_series += 1
            log.debug("Countdown over.")

        repetition_ended = repetition_ended or (self.countdown == 0)

        self.countdown -= 1

        if repetition_ended:
            if self.timed_out and (self.countdown < 0):
                self.n_timeout -= 1
                if self.n_timeout == 0:
                    log.debug("Maximum number of timeouts reached.")
                    raise TimeoutError
            elif not self.timed_out and (self.countdown < 0):
                log.debug("First timeout reached.")
                self.timed_out = True
                self.n_timeout = int(self.n_timeout / self.rep_timeout)
            else:
                log.debug("No timeout reached.")
                self.timed_out = False
                self.n_timeout = int(self.n_timeout / self.rep_timeout)

            if len(set(self.outputs)) == 1 and self.outputs[0] == 0:
                #timed_out_rep += 1
                log.debug("Timeout reached: no repetition completed.")
                raise NoneRepetitionException
            else:
                if self.__check_repetition__():
                    log.debug("All movements where correct!")
                    log.info("Good repetition!")
                    self.num_good_reps += 1
                else:
                    log.info("Bad repetition!")
                    self.num_bad_reps += 1
                    raise BadRepetitionException

            if self.num_good_reps == self.n_repetition:
                log.info("Completed exercise.")
                raise CompleteExerciseException
            