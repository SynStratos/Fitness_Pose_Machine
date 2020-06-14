import json


class Exercise:
    """

    """
    def __init__(self, config, side):
        if side not in ['s_e', 's_w']: raise Exception("Unexpected 'side' value.")
        config = json.load(config)
        self.name = config["exercise_name"]
        self.angles = config["angles_names"]
        self.angles_index = config["angles_to_check"]["side"]
        self.push_pull = config["push_pull"]
        self.mins = config["mins"]
        self.maxs = config["maxs"]
        self.mids = config["mids"]
        self.angles_order = config["angles_order"]
        self.rep_timeout = config["repetition_timeout"]
        self.tot_timeout = config["total_timeout"]
        self.n_repetition = config["n_repetition"]

