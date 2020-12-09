from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, ListEndpoint, \
    IncludeCustomEndpoint, UuidEndpoint, ChannelIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.memberships import PNRemoveMembershipsResult


class RemoveMemberships(ObjectsEndpoint, UuidEndpoint, ListEndpoint, IncludeCustomEndpoint,
                        ChannelIncludeEndpoint):
    REMOVE_MEMBERSHIPS_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        ListEndpoint.__init__(self)
        UuidEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        ChannelIncludeEndpoint.__init__(self)

        self._channel_memberships = []

    def channel_memberships(self, channel_memberships):
        self._channel_memberships = list(channel_memberships)
        return self

    def build_path(self):
        return RemoveMemberships.REMOVE_MEMBERSHIPS_PATH % (self.pubnub.config.subscribe_key, self._effective_uuid())

    def build_data(self):
        channel_memberships_to_delete = []

        for channel_membership in self._channel_memberships:
            channel_memberships_to_delete.append(channel_membership.to_payload_dict())

        payload = {
            "set": [],
            "delete": channel_memberships_to_delete
        }
        return utils.write_value_as_string(payload)

    def validate_specific_params(self):
        self._validate_uuid()

    def create_response(self, envelope):
        return PNRemoveMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNRemoveMembershipsOperation

    def name(self):
        return "Remove Memberships"

    def http_method(self):
        return HttpMethod.PATCH
