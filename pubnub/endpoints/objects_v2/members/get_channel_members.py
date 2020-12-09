from pubnub.endpoints.objects_v2.objects_endpoint import ObjectsEndpoint, IncludeCustomEndpoint, \
    ChannelEndpoint, ListEndpoint, UUIDIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.objects_v2.channel_members import PNGetChannelMembersResult


class GetChannelMembers(ObjectsEndpoint, ChannelEndpoint, ListEndpoint, IncludeCustomEndpoint,
                        UUIDIncludeEndpoint):
    GET_CHANNEL_MEMBERS_PATH = "/v2/objects/%s/channels/%s/uuids"

    def __init__(self, pubnub):
        ObjectsEndpoint.__init__(self, pubnub)
        ChannelEndpoint.__init__(self)
        ListEndpoint.__init__(self)
        IncludeCustomEndpoint.__init__(self)
        UUIDIncludeEndpoint.__init__(self)

    def build_path(self):
        return GetChannelMembers.GET_CHANNEL_MEMBERS_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def validate_specific_params(self):
        self._validate_channel()

    def create_response(self, envelope):
        return PNGetChannelMembersResult(envelope)

    def operation_type(self):
        return PNOperationType.PNGetChannelMembersOperation

    def name(self):
        return "Get Channel Members"

    def http_method(self):
        return HttpMethod.GET
