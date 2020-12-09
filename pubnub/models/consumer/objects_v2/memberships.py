from abc import abstractmethod, ABCMeta

from pubnub.models.consumer.objects_v2.page import PNPageable


class PNChannelMembership:
    __metaclass__ = ABCMeta

    def __init__(self, channel):
        self._channel = channel

    @staticmethod
    def channel(channel):
        return JustChannel(channel)

    @staticmethod
    def channel_with_custom(channel, custom):
        return ChannelWithCustom(channel, custom)

    @abstractmethod
    def to_payload_dict(self):
        return None


class JustChannel(PNChannelMembership):
    def __init__(self, channel):
        PNChannelMembership.__init__(self, channel)

    def to_payload_dict(self):
        return {
            "channel": {
                "id": str(self._channel)
            }
        }


class ChannelWithCustom(PNChannelMembership):
    def __init__(self, channel, custom):
        PNChannelMembership.__init__(self, channel)
        self._custom = custom

    def to_payload_dict(self):
        return {
            "channel": {
                "id": str(self._channel)
            },
            "custom": dict(self._custom)
        }


class PNSetMembershipsResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Set Memberships metatdata: %s" % self.data


class PNGetMembershipsResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get Memberships metatdata: %s" % self.data


class PNRemoveMembershipsResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Remove Memberships metatdata: %s" % self.data


class PNManageMembershipsResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Manage Channel Members metatdata: %s" % self.data


class PNMembershipResult(object):
    def __init__(self, event, data):
        self.data = data
        self.event = event

    def __str__(self):
        return "Membership %s event with data: %s" % (self.event, self.data)
