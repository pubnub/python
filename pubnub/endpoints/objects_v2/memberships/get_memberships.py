from pubnub.endpoints.objects_v2.objects_endpoint import IncludeCapableEndpoint, ObjectsEndpoint, \
    IncludeCustomEndpoint, UuidEndpoint, ListEndpoint, ChannelIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.common import MembershipIncludes
from pubnub.models.consumer.objects_v2.memberships import PNGetMembershipsResult
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.structures import Envelope


class PNGetMembershipsResultEnvelope(Envelope):
    result: PNGetMembershipsResult
    status: PNStatus


class GetMemberships(ObjectsEndpoint, UuidEndpoint, ListEndpoint, IncludeCustomEndpoint, IncludeCapableEndpoint,
                     ChannelIncludeEndpoint):
    GET_MEMBERSHIPS_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub, uuid: str = None, include_custom: bool = False, limit: int = None, filter: str = None,
                 include_total_count: bool = None, sort_keys: list = None, page: PNPage = None,
                 include: MembershipIncludes = None):
        ObjectsEndpoint.__init__(self, pubnub)
        IncludeCapableEndpoint.__init__(self, include=include)
        UuidEndpoint.__init__(self, uuid=uuid)
        ListEndpoint.__init__(self, limit=limit, filter=filter, include_total_count=include_total_count,
                              sort_keys=sort_keys, page=page)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        ChannelIncludeEndpoint.__init__(self)

    def build_path(self):
        return GetMemberships.GET_MEMBERSHIPS_PATH % (self.pubnub.config.subscribe_key, self._effective_uuid())

    def validate_specific_params(self):
        self._validate_uuid()

    def include(self, includes: MembershipIncludes) -> 'GetMemberships':
        """
        Include additional information in the membership response.

        Parameters
        ----------
        includes : MembershipIncludes
            The additional information to include in the membership response.

        See Also
        --------
        pubnub.models.consumer.objects_v2.common.MembershipIncludese : For details on the available includes.

        Returns
        -------
        self : GetMemberships
        """
        super().include(includes)
        return self

    def create_response(self, envelope) -> PNGetMembershipsResult:
        return PNGetMembershipsResult(envelope)

    def sync(self) -> PNGetMembershipsResultEnvelope:
        return PNGetMembershipsResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNGetMembershipsOperation

    def name(self):
        return "Get Memberships"

    def http_method(self):
        return HttpMethod.GET
