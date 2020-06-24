import json
from exceptions import *
from copy import copy

from logger import log


class Exercise:
    mids = None

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

    CHECKS = []

    def __init__(self, config, side, fps):
        if side not in ['s_e', 's_w']: raise Exception("Unexpected 'side' value.")
        with open(config) as f:
            config = json.load(f)

        self.config = config
        self.name = config["exercise_name"]

        log.info("Creating a {} exercise!".format(self.name))

        self.angles = config["angles_names"]
        # select which angles have to be checked for each respective side
        self.angles_index = config["angles_to_check"][side]
        # define if the expected movement for each angle is a push or a pull
        self.push_pull = config["push_pull"]
        self.mins = config["mins"]
        self.maxs = config["maxs"]
        self.mids = config["mids"]
        # expected order of angles reaching spikes
        self.angles_order = config["angles_order"]
        # timeout for a single repetition expressed in seconds
        self.rep_timeout = config["repetition_timeout"]
        # maximum consecutive timeouts (expressed in seconds) before exiting the session
        self.tot_timeout = config["total_timeout"]
        # number of total repetitions expected to end the exercise
        self.n_repetition = config["n_repetition"]
        # tolerance for the high threshold of angles' movements
        self.tolerance = config["tolerance"]
        # number of times each angle has to reach the threshold for the repetition to be good
        self.number_of_spikes = copy(config["number_of_spikes"])
        self.n_angles = len(self.angles_index)
        # set of further check methods to be applied to some specific angles (works on indexes)
        self.CHECKS = [None] * self.n_angles

        self.fps = fps

        # counter of frame for each repetition
        self.time = 0

        # array to track the status of each angle
        self.states = [0]*self.n_angles
        # array to track the output of each angle
        self.outputs = [0]*self.n_angles
        # array to track the timestamp in which each angle reaches its threshold/good condition
        self.timestamps = [0]*self.n_angles
        # calculate number of timeouts before exiting
        self.n_timeout = int(self.tot_timeout / self.rep_timeout)
        # countdown before a single repetition timeout calculated in frames
        self.countdown = int(fps * self.rep_timeout)
        # variable to track if a timeout has been reached
        self.timed_out = False

        self.num_good_reps = 0
        self.num_bad_reps = 0
        self.time_out_series = 0

        self.index_to_keep = []

    def __reset__(self):
        """
        resets all the counters and tracking arrays at the end of a repetition (good, bad or timeout)
        """
        log.debug("Resetting exercise variables after a single repetition.")
        self.states = [0] * self.n_angles
        for i in self.index_to_keep:
            self.states[i] = 1
        self.index_to_keep = []
        self.outputs = [0] * self.n_angles
        self.timestamps = [0] * self.n_angles

        self.number_of_spikes = copy(self.config["number_of_spikes"])

        # self.n_timeout = int(self.tot_timeout / self.rep_timeout)
        self.countdown = int(self.fps * self.rep_timeout)

    def __check_pull_frame__(self, angle, index, _min, _max, mid_point, **kwargs):
        """
        method that checks a pull movement frame.
        the complementary value is calculated for each in order to use the method to check a push frame
        """
        angle = abs(180 - angle)
        _min = abs(180 - _min)
        _max = abs(180 - _max)
        mid_point = abs(180 - mid_point)

        self.__check_push_frame__(angle, index, _min, _max, mid_point, **kwargs)

    def __check_push_frame__(self, angle, index, _min, _max, mid_point, **kwargs):
        """
        method that checks a push movement frame.
        @param angle: the value of the angle to be checked
        @param index: the index corresponding to the angle in each structure contained in the class
        @param _min: minimum value for that angle
        @param _max: maximum value for that angle
        @param mid_point: mid value for that angle
        """
        print("index: ", index)
        print("checks: ", str(self.CHECKS))
        if self.CHECKS[index]:
            try:
                self.outputs[index] = 1 if (self.CHECKS[index](angle, **kwargs) or self.outputs[index] == 1) else self.outputs[index]
                return
                #TODO: esci quando fa controllo - gestisco andamento dell'angolo con un altro 'angolo' in array ma con stesso indice

            except Exception as e:
                log.error(str(e))
                raise Exception(e)
        # TODO: angoli di cui controllare SOLO le condizioni parametrizzate in funzione
        # TODO: angoli di cui servono controllare i picchi e le condizioni

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
            elif (_max - self.tolerance[index]) <= angle <= (_max + self.tolerance[index]):
                # goes directly to top value, maybe skipped frames
                self.states[index] = 3

        # state 'rep_going'
        elif self.states[index] == 2:
            # goes to 'top'
            if (_max - self.tolerance[index]) <= angle <= (_max + self.tolerance[index]):
                self.states[index] = 3
            # goes back to 'min' without completing the repetition
            elif angle <= _min:
                self.timestamps[index] = self.time

                self.number_of_spikes[index] -= 1
                if self.number_of_spikes[index] == 0:
                    self.outputs[index] = 2  # set to bad repetition

                self.states[index] = 0
            # goes directly over the top value, maybe skipped frames
            elif angle > (_max + self.tolerance[index]):
                self.timestamps[index] = self.time
                self.number_of_spikes[index] -= 1
                if self.number_of_spikes[index] == 0:
                    self.outputs[index] = 2  # set to bad repetition
                self.states[index] = 4

        # state 'top'
        elif self.states[index] == 3:
            # goes back to 'min'
            if angle <= _min:
                self.timestamps[index] = self.time
                self.number_of_spikes[index] -= 1
                if self.number_of_spikes[index] == 0:
                    self.outputs[index] = 1  # repetition correctly completed
                self.states[index] = 0
            # goes over the top value
            elif angle > (_max + self.tolerance[index]):
                self.timestamps[index] = self.time
                self.number_of_spikes[index] -= 1
                if self.number_of_spikes[index] == 0:
                    self.outputs[index] = 2  # set to bad repetition
                self.states[index] = 4

        # state 'over_top'
        elif self.states[index] == 4:
            # goes back to min
            if angle <= _min:
                self.states[index] = 0

    def __check_order__(self):
        """
        @return: True se ordine corretto, False se ordine errato
        """
        if not self.angles_order:
            # If it is not needed to check angles order, value in the json must be set to None
            return True, ""
        elif len(self.angles_order) < 2:
            raise Exception("cant check order of a single element")

        for i, o in enumerate(self.angles_order):
            for angle_x in o:
                for oo in self.angles_order[i + 1:]:
                    for angle_y in oo:
                        if (self.timestamps[angle_x] >= self.timestamps[angle_y]) and (self.timestamps[angle_x] > 0) and (self.timestamps[angle_y] > 0):
                            s = "Wrong order: you moved your {} before your {}.".format(self.angles[angle_x], self.angles[angle_y])
                            return False, s

        return True, ""

    def __check_repetition__(self):
        """
        method that checks that a ended repetition was good or bad. if bad it outputs the kind of error.
        """
        if len(set(self.outputs)) == 1 and self.outputs[0] == 1:
            return self.__check_order__()
        else:
            if len(set(self.outputs)) == 1 and self.outputs[0] == 2:
                s = "All movements where wrong!"
            else:
                s = ""
                for i, o in enumerate(self.outputs):
                    s += "Movement for {} was {}! \n".format(self.angles[i], self.OUTPUTS[o])
            return False, s

    def process_frame(self, frame, exercise_over=False, **kwargs):
        """
        ingest the frame and check each angle contained in it.
        """
        if exercise_over:
            repetition_ended = True
        else:
            repetition_ended = False
            for i, angle in enumerate(self.angles_index):

                if self.push_pull[i] == "push":
                    self.__check_push_frame__(frame[angle], index=i, _min=self.mins[i], _max=self.maxs[i], mid_point=self.mids[i], **kwargs)
                elif self.push_pull[i] == "pull":
                    self.__check_pull_frame__(frame[angle], index=i, _min=self.mins[i], _max=self.maxs[i], mid_point=self.mids[i], **kwargs)

                repetition_ended = False

                if self.outputs[i] in [1, 2] and self.states[i] == 1:
                    repetition_ended = True
                    self.index_to_keep.append(i)
        self.time += 1
        log.debug("states: " + str(self.states))
        log.debug("outputs: " + str(self.outputs))
        log.debug("spikes: " + str(self.number_of_spikes))
        if self.countdown == 0:
            self.time_out_series += 1
            log.debug("Countdown over.")

        repetition_ended = repetition_ended or (self.countdown == 0)

        self.countdown -= 1

        if repetition_ended:
            if self.timed_out and (self.countdown < 0):
                self.n_timeout -= 1
                if self.n_timeout == 0:
                    log.info("Maximum number of timeouts reached.")
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
                self.__reset__()
                log.info("No repetition completed.")
                raise NoneRepetitionException
            else:
                good, message = self.__check_repetition__()
                if good:
                    log.debug("All movements where correct!")
                    log.info("Good repetition!")
                    self.__reset__()
                    self.num_good_reps += 1

                    if self.num_good_reps == self.n_repetition:
                        log.info("Completed exercise.")
                        raise CompleteExerciseException

                    raise GoodRepetitionException
                else:
                    log.info("Bad repetition!")
                    self.num_bad_reps += 1
                    self.__reset__()
                    raise BadRepetitionException(message)
