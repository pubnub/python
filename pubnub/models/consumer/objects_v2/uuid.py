from pubnub.models.consumer.objects_v2.page import PNPageable


class PNSetUUIDMetadataResult(object):
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Set UUID metatdata: %s" % self.data


class PNGetUUIDMetadataResult(object):
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get UUID metatdata: %s" % self.data


class PNRemoveUUIDMetadataResult(object):
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get UUID metatdata: %s" % self.data


class PNGetAllUUIDMetadataResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get all UUID metatdata: %s" % self.data


class PNUUIDMetadataResult(object):
    def __init__(self, event, data):
        self.data = data
        self.event = event

    def __str__(self):
        return "UUID %s event with data: %s" % (self.event, self.data)
