class PNErrorData():
    def __init__(self, information, exception):
        assert isinstance(information, str)
        assert isinstance(exception, Exception)

        self.information = information
        self.exception = exception
