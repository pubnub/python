from typing import List
from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import IncludeCapableEndpoint, ObjectsEndpoint, \
    IncludeCustomEndpoint, ListEndpoint, ChannelIncludeEndpoint, UuidEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.common import MembershipIncludes
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership, PNRemoveMembershipsResult
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.structures import Envelope


class PNRemoveMembershipsResultEnvelope(Envelope):
    result: PNRemoveMembershipsResult
    status: PNStatus


class RemoveMemberships(ObjectsEndpoint, ListEndpoint, IncludeCustomEndpoint, IncludeCapableEndpoint,
                        ChannelIncludeEndpoint, UuidEndpoint):
    REMOVE_MEMBERSHIPS_PATH = "/v2/objects/%s/uuids/%s/channels"

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

    def include(self, includes: MembershipIncludes) -> 'RemoveMemberships':
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
        self : RemoveMemberships
        """
        super().include(includes)
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

    def create_response(self, envelope) -> PNRemoveMembershipsResult:
        return PNRemoveMembershipsResult(envelope)

    def sync(self) -> PNRemoveMembershipsResultEnvelope:
        return PNRemoveMembershipsResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNRemoveMembershipsOperation

    def name(self):
        return "Remove Memberships"

    def http_method(self):
        return HttpMethod.PATCH
