class PNEntityResult(object):
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return self._description % self.data


class PNEntityPageableResult(PNEntityResult):
    def __init__(self, result):
        super().__init__(result)
