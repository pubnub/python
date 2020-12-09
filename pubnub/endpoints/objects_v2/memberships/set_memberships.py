from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, IncludeCustomEndpoint, \
    ListEndpoint, ChannelIncludeEndpoint, UuidEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.memberships import PNSetMembershipsResult


class SetMemberships(ObjectsEndpoint, ListEndpoint, IncludeCustomEndpoint,
                     ChannelIncludeEndpoint, UuidEndpoint):
    SET_MEMBERSHIP_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        UuidEndpoint.__init__(self)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        ChannelIncludeEndpoint.__init__(self)

        self._channel_memberships = []

    def channel_memberships(self, channel_memberships):
        self._channel_memberships = list(channel_memberships)
        return self

    def validate_specific_params(self):
        self._validate_uuid()

    def build_path(self):
        return SetMemberships.SET_MEMBERSHIP_PATH % (self.pubnub.config.subscribe_key, self._effective_uuid())

    def build_data(self):
        channel_memberships_to_set = []

        for channel_membership in self._channel_memberships:
            channel_memberships_to_set.append(channel_membership.to_payload_dict())

        payload = {
            "set": channel_memberships_to_set,
            "delete": []
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope):
        return PNSetMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNSetMembershipsOperation

    def name(self):
        return "Set Memberships"

    def http_method(self):
        return HttpMethod.PATCH
