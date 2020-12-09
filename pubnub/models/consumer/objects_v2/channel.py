from pubnub.models.consumer.objects_v2.page import PNPageable


class PNSetChannelMetadataResult(object):
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Set Channel metatdata: %s" % self.data


class PNGetChannelMetadataResult(object):
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get Channel metatdata: %s" % self.data


class PNRemoveChannelMetadataResult(object):
    def __init__(self, result):
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get Channel metatdata: %s" % self.data


class PNGetAllChannelMetadataResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get all Channel metatdata: %s" % self.data


class PNChannelMetadataResult(object):
    def __init__(self, event, data):
        self.data = data
        self.event = event

    def __str__(self):
        return "Channel %s event with data: %s" % (self.event, self.data)
