class BadRepetitionException(Exception):
    """
    exception raised for a bad repetition
    """
    def __init__(self, *args):
        super(BadRepetitionException, self).__init__(*args)


class NoneRepetitionException(Exception):
    """
    exception raised for repetition ended without movements
    """
    def __init__(self, *args):
        super(NoneRepetitionException, self).__init__(*args)


class CompleteExerciseException(Exception):
    """
    exception raised when all the good repetitions of an exercise have been executed
    """
    def __init__(self, *args):
        super(CompleteExerciseException, self).__init__(*args)


class GoodRepetitionException(Exception):
    """
    exception raised for a good repetition
    """
    def __init__(self, *args):
        super(GoodRepetitionException, self).__init__(*args)


class NotFoundPersonException(Exception):
    """
    exception raised when a person is not found during the pose estimation
    """
    def __init__(self, *args):
        super(NotFoundPersonException, self).__init__(*args)


class FeetException(Exception):
    """
    exception raised when feet can't be found in the frame
    """
    def __init__(self, *args):
        super(FeetException, self).__init__(*args)