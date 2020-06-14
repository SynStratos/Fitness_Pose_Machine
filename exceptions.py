class BadRepetitionException(Exception):
    def __init__(self, *args):
        super(BadRepetitionException, self).__init__(*args)


class NoneRepetitionException(Exception):
    def __init__(self, *args):
        super(NoneRepetitionException, self).__init__(*args)

