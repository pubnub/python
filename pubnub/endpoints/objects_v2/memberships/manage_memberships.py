from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, ListEndpoint, \
    IncludeCustomEndpoint, UuidEndpoint, ChannelIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod

from pubnub.models.consumer.objects_v2.memberships import PNManageMembershipsResult


class ManageMemberships(ObjectsEndpoint, UuidEndpoint, ListEndpoint, IncludeCustomEndpoint,
                        ChannelIncludeEndpoint):
    MANAGE_MEMBERSHIPS_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        UuidEndpoint.__init__(self)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        ChannelIncludeEndpoint.__init__(self)

        self._channel_memberships_to_set = []
        self._channel_memberships_to_remove = []

    def set(self, channel_memberships_to_set):
        self._channel_memberships_to_set = list(channel_memberships_to_set)
        return self

    def remove(self, channel_memberships_to_remove):
        self._channel_memberships_to_remove = list(channel_memberships_to_remove)
        return self

    def validate_specific_params(self):
        self._validate_uuid()

    def build_path(self):
        return ManageMemberships.MANAGE_MEMBERSHIPS_PATH % (self.pubnub.config.subscribe_key, self._effective_uuid())

    def build_data(self):
        channel_memberships_to_set = []
        channel_memberships_to_remove = []

        for channel_membership in self._channel_memberships_to_set:
            channel_memberships_to_set.append(channel_membership.to_payload_dict())

        for channel_membership in self._channel_memberships_to_remove:
            channel_memberships_to_remove.append(channel_membership.to_payload_dict())

        payload = {
            "set": channel_memberships_to_set,
            "delete": channel_memberships_to_remove
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope):
        return PNManageMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNManageMembershipsOperation

    def name(self):
        return "Manage Memberships"

    def http_method(self):
        return HttpMethod.PATCH
