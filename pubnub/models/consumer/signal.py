class PNSignalResult(object):
    def __init__(self, result):
        """
        Representation of signal server response

        :param result: result of signal operation
        """
        self.timetoken = result[2]
        self._result = result

    def __str__(self):
        return "Signal success with timetoken %s" % self.timetoken
