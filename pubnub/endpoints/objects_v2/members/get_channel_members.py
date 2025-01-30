from pubnub.endpoints.objects_v2.objects_endpoint import IncludeCapableEndpoint, ObjectsEndpoint, \
    IncludeCustomEndpoint, ChannelEndpoint, ListEndpoint, UUIDIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel_members import PNGetChannelMembersResult
from pubnub.models.consumer.objects_v2.common import MemberIncludes
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.structures import Envelope


class PNGetChannelMembersResultEnvelope(Envelope):
    result: PNGetChannelMembersResult
    status: PNStatus


class GetChannelMembers(ObjectsEndpoint, ChannelEndpoint, ListEndpoint, IncludeCustomEndpoint,
                        UUIDIncludeEndpoint, IncludeCapableEndpoint):
    GET_CHANNEL_MEMBERS_PATH = "/v2/objects/%s/channels/%s/uuids"

    def __init__(self, pubnub, channel: str = None, include_custom: bool = None,
                 limit: int = None, filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                 page: PNPage = None, include: MemberIncludes = None):
        ObjectsEndpoint.__init__(self, pubnub)
        IncludeCapableEndpoint.__init__(self, include)
        ChannelEndpoint.__init__(self, channel=channel)
        ListEndpoint.__init__(self, limit=limit, filter=filter, include_total_count=include_total_count,
                              sort_keys=sort_keys, page=page)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        UUIDIncludeEndpoint.__init__(self)

    def build_path(self):
        return GetChannelMembers.GET_CHANNEL_MEMBERS_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def validate_specific_params(self):
        self._validate_channel()

    def include(self, includes: MemberIncludes) -> 'GetChannelMembers':
        super().include(includes)
        return self

    def create_response(self, envelope) -> PNGetChannelMembersResult:
        return PNGetChannelMembersResult(envelope)

    def sync(self) -> PNGetChannelMembersResultEnvelope:
        return PNGetChannelMembersResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNGetChannelMembersOperation

    def name(self):
        return "Get Channel Members"

    def http_method(self):
        return HttpMethod.GET
