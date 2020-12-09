from abc import abstractmethod, ABCMeta

from pubnub.models.consumer.objects_v2.page import PNPageable


class PNUUID:
    __metaclass__ = ABCMeta

    def __init__(self, uuid):
        self._uuid = uuid

    @staticmethod
    def uuid(uuid):
        return JustUUID(uuid)

    @staticmethod
    def uuid_with_custom(uuid, custom):
        return UUIDWithCustom(uuid, custom)

    @abstractmethod
    def to_payload_dict(self):
        return None


class JustUUID(PNUUID):
    def to_payload_dict(self):
        return {
            "uuid": {
                "id": str(self._uuid)
            }
        }


class UUIDWithCustom(PNUUID):
    def __init__(self, uuid, custom):
        PNUUID.__init__(self, uuid)
        self._custom = custom

    def to_payload_dict(self):
        return {
            "uuid": {
                "id": str(self._uuid)
            },
            "custom": dict(self._custom)
        }


class PNSetChannelMembersResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Set Channel Members metatdata: %s" % self.data


class PNGetChannelMembersResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get Channel Members metatdata: %s" % self.data


class PNRemoveChannelMembersResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Remove Channel Members metatdata: %s" % self.data


class PNManageChannelMembersResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Manage Channel Members metatdata: %s" % self.data
