from typing import List
from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import IncludeCapableEndpoint, ObjectsEndpoint, \
    IncludeCustomEndpoint, ListEndpoint, ChannelIncludeEndpoint, UuidEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.common import MembershipIncludes
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership, PNSetMembershipsResult
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.structures import Envelope


class PNSetMembershipsResultEnvelope(Envelope):
    result: PNSetMembershipsResult
    status: PNStatus


class SetMemberships(ObjectsEndpoint, ListEndpoint, IncludeCustomEndpoint, IncludeCapableEndpoint,
                     ChannelIncludeEndpoint, UuidEndpoint):
    SET_MEMBERSHIP_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub, uuid: str = None, channel_memberships: List[PNChannelMembership] = None,
                 include_custom: bool = False, limit: int = None, filter: str = None, include_total_count: bool = None,
                 sort_keys: list = None, page: PNPage = None, include: MembershipIncludes = None):
        ObjectsEndpoint.__init__(self, pubnub)
        IncludeCapableEndpoint.__init__(self, include=include)
        UuidEndpoint.__init__(self, uuid=uuid)
        ListEndpoint.__init__(self, limit=limit, filter=filter, include_total_count=include_total_count,
                              sort_keys=sort_keys, page=page)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        ChannelIncludeEndpoint.__init__(self)

        self._channel_memberships = []
        if channel_memberships:
            utils.extend_list(self._channel_memberships, channel_memberships)

    def channel_memberships(self, channel_memberships):
        utils.extend_list(self._channel_memberships, channel_memberships)
        return self

    def validate_specific_params(self):
        self._validate_uuid()

    def include(self, includes: MembershipIncludes) -> 'SetMemberships':
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
        self : SetMemberships
        """
        super().include(includes)
        return self

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

    def create_response(self, envelope) -> PNSetMembershipsResult:
        return PNSetMembershipsResult(envelope)

    def sync(self) -> PNSetMembershipsResultEnvelope:
        return PNSetMembershipsResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNSetMembershipsOperation

    def name(self):
        return "Set Memberships"

    def http_method(self):
        return HttpMethod.PATCH
