from pubnub.models.consumer.objects_v2.page import PNPageable


class PNEntityResult(object):
    def __init__(self, result):
        self.data = result["data"] if "data" in result else None
        self.status = result["status"]

    def __str__(self):
        return self._description % self.data


class PNEntityPageableResult(PNEntityResult, PNPageable):
    def __init__(self, result):
        PNEntityResult.__init__(self, result)
        PNPageable.__init__(self, result)
