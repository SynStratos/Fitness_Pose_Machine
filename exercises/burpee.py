from exercises.exercise import Exercise


class Burpee(Exercise):
    def __init__(self, config, side, fps):
        super().__init__(config, side, fps)