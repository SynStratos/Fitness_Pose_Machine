class BadRepetitionException(Exception):
    def __init__(self, *args):
        super(BadRepetitionException, self).__init__(*args)


class NoneRepetitionException(Exception):
    def __init__(self, *args):
        super(NoneRepetitionException, self).__init__(*args)


class CompleteExerciseException(Exception):
    def __init__(self, *args):
        super(CompleteExerciseException, self).__init__(*args)


class GoodRepetitionException(Exception):
    def __init__(self, *args):
        super(GoodRepetitionException, self).__init__(*args)