from exercises.exercise import Exercise

ex_config = "./config/thruster_config.json"


class Thruster(Exercise):
    def __init__(self, config, side, fps):
        config = ex_config
        super().__init__(config, side, fps)

