from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, ListEndpoint, \
    IncludeCustomEndpoint, ChannelEndpoint, UUIDIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.channel_members import PNManageChannelMembersResult


class ManageChannelMembers(ObjectsEndpoint, ChannelEndpoint, ListEndpoint, IncludeCustomEndpoint,
                           UUIDIncludeEndpoint):
    MANAGE_CHANNELS_MEMBERS_PATH = "/v2/objects/%s/channels/%s/uuids"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        ChannelEndpoint.__init__(self)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        UUIDIncludeEndpoint.__init__(self)

        self._uuids_to_set = []
        self._uuids_to_remove = []

    def set(self, uuids_to_set):
        self._uuids_to_set = list(uuids_to_set)
        return self

    def remove(self, uuids_to_remove):
        self._uuids_to_remove = list(uuids_to_remove)
        return self

    def validate_specific_params(self):
        self._validate_channel()

    def build_path(self):
        return ManageChannelMembers.MANAGE_CHANNELS_MEMBERS_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def build_data(self):
        uuids_to_set = []
        uuids_to_remove = []

        for uuid in self._uuids_to_set:
            uuids_to_set.append(uuid.to_payload_dict())

        for uuid in self._uuids_to_remove:
            uuids_to_remove.append(uuid.to_payload_dict())

        payload = {
            "set": uuids_to_set,
            "delete": uuids_to_remove
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope):
        return PNManageChannelMembersResult(envelope)

    def operation_type(self):
        return PNOperationType.PNManageChannelMembersOperation

    def name(self):
        return "Manage Channels Members"

    def http_method(self):
        return HttpMethod.PATCH
