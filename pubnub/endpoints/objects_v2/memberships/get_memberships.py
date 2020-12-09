from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, IncludeCustomEndpoint, \
    UuidEndpoint, ListEndpoint, ChannelIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.memberships import PNGetMembershipsResult


class GetMemberships(ObjectsEndpoint, UuidEndpoint, ListEndpoint, IncludeCustomEndpoint,
                     ChannelIncludeEndpoint):
    GET_MEMBERSHIPS_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        UuidEndpoint.__init__(self)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        ChannelIncludeEndpoint.__init__(self)

    def build_path(self):
        return GetMemberships.GET_MEMBERSHIPS_PATH % (self.pubnub.config.subscribe_key, self._effective_uuid())

    def validate_specific_params(self):
        self._validate_uuid()

    def create_response(self, envelope):
        return PNGetMembershipsResult(envelope)

    def operation_type(self):
        return PNOperationType.PNGetMembershipsOperation

    def name(self):
        return "Get Memberships"

    def http_method(self):
        return HttpMethod.GET
