from typing import List
from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import IncludeCapableEndpoint, ObjectsEndpoint, ListEndpoint, \
    IncludeCustomEndpoint, UuidEndpoint, ChannelIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod

from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.common import MembershipIncludes
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership, PNManageMembershipsResult
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.structures import Envelope


class PNManageMembershipsResultEnvelope(Envelope):
    result: PNManageMembershipsResult
    status: PNStatus


class ManageMemberships(ObjectsEndpoint, UuidEndpoint, ListEndpoint, IncludeCustomEndpoint, IncludeCapableEndpoint,
                        ChannelIncludeEndpoint):
    MANAGE_MEMBERSHIPS_PATH = "/v2/objects/%s/uuids/%s/channels"

    def __init__(self, pubnub, uuid: str = None, channel_memberships_to_set: List[PNChannelMembership] = None,
                 channel_memberships_to_remove: List[PNChannelMembership] = None, include_custom: bool = False,
                 limit: int = None, filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                 page: PNPage = None, include: MembershipIncludes = None):

        ObjectsEndpoint.__init__(self, pubnub)
        IncludeCapableEndpoint.__init__(self, include=include)
        UuidEndpoint.__init__(self, uuid=uuid)
        ListEndpoint.__init__(self, limit=limit, filter=filter, include_total_count=include_total_count,
                              sort_keys=sort_keys, page=page)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        ChannelIncludeEndpoint.__init__(self)

        self._channel_memberships_to_set = []
        if channel_memberships_to_set:
            utils.extend_list(self._channel_memberships_to_set, channel_memberships_to_set)

        self._channel_memberships_to_remove = []
        if channel_memberships_to_remove:
            utils.extend_list(self._channel_memberships_to_remove, channel_memberships_to_remove)

    def set(self, channel_memberships_to_set: List[PNChannelMembership]) -> 'ManageMemberships':
        self._channel_memberships_to_set = list(channel_memberships_to_set)
        return self

    def remove(self, channel_memberships_to_remove: List[PNChannelMembership]) -> 'ManageMemberships':
        self._channel_memberships_to_remove = list(channel_memberships_to_remove)
        return self

    def include(self, includes: MembershipIncludes) -> 'ManageMemberships':
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

    def create_response(self, envelope) -> PNManageMembershipsResult:
        return PNManageMembershipsResult(envelope)

    def sync(self) -> PNManageMembershipsResultEnvelope:
        return PNManageMembershipsResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNManageMembershipsOperation

    def name(self):
        return "Manage Memberships"

    def http_method(self):
        return HttpMethod.PATCH
