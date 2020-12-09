from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, ChannelEndpoint, ListEndpoint, \
    IncludeCustomEndpoint, UUIDIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.channel_members import PNRemoveChannelMembersResult


class RemoveChannelMembers(ObjectsEndpoint, ChannelEndpoint, ListEndpoint, IncludeCustomEndpoint,
                           UUIDIncludeEndpoint):
    REMOVE_CHANNEL_MEMBERS_PATH = "/v2/objects/%s/channels/%s/uuids"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self)
        ChannelEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        UUIDIncludeEndpoint.__init__(self)

        self._uuids = []

    def uuids(self, uuids):
        self._uuids = list(uuids)
        return self

    def build_path(self):
        return RemoveChannelMembers.REMOVE_CHANNEL_MEMBERS_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def build_data(self):
        uuids_to_delete = []

        for uuid in self._uuids:
            uuids_to_delete.append(uuid.to_payload_dict())

        payload = {
            "set": [],
            "delete": uuids_to_delete
        }
        return utils.write_value_as_string(payload)

    def validate_specific_params(self):
        self._validate_channel()

    def create_response(self, envelope):
        return PNRemoveChannelMembersResult(envelope)

    def operation_type(self):
        return PNOperationType.PNRemoveChannelMembersOperation

    def name(self):
        return "Remove Channel Members"

    def http_method(self):
        return HttpMethod.PATCH
