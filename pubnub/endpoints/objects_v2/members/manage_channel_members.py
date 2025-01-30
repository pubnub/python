from typing import List
from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import IncludeCapableEndpoint, ObjectsEndpoint, ListEndpoint, \
    IncludeCustomEndpoint, ChannelEndpoint, UUIDIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel_members import PNUUID, PNManageChannelMembersResult
from pubnub.models.consumer.objects_v2.common import MembershipIncludes
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.structures import Envelope


class PNManageChannelMembersResultEnvelope(Envelope):
    result: PNManageChannelMembersResult
    status: PNStatus


class ManageChannelMembers(ObjectsEndpoint, ChannelEndpoint, ListEndpoint, IncludeCustomEndpoint,
                           IncludeCapableEndpoint, UUIDIncludeEndpoint):
    MANAGE_CHANNELS_MEMBERS_PATH = "/v2/objects/%s/channels/%s/uuids"

    def __init__(self, pubnub, channel: str = None, uuids_to_set: List[PNUUID] = None,
                 uuids_to_remove: List[PNUUID] = None, include_custom: bool = None, limit: int = None,
                 filter: str = None, include_total_count: bool = None, sort_keys: list = None, page: PNPage = None,
                 include: MembershipIncludes = None):
        ObjectsEndpoint.__init__(self, pubnub)
        IncludeCapableEndpoint.__init__(self, include)
        ChannelEndpoint.__init__(self, channel=channel)
        ListEndpoint.__init__(self, limit=limit, filter=filter, include_total_count=include_total_count,
                              sort_keys=sort_keys, page=page)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        UUIDIncludeEndpoint.__init__(self)

        self._uuids_to_set = []
        if uuids_to_set:
            utils.extend_list(self._uuids_to_set, uuids_to_set)
        self._uuids_to_remove = []
        if uuids_to_remove:
            utils.extend_list(self._uuids_to_remove, uuids_to_remove)

    def set(self, uuids_to_set: List[PNUUID]) -> 'ManageChannelMembers':
        self._uuids_to_set = list(uuids_to_set)
        return self

    def remove(self, uuids_to_remove: List[PNUUID]) -> 'ManageChannelMembers':
        self._uuids_to_remove = list(uuids_to_remove)
        return self

    def validate_specific_params(self):
        self._validate_channel()

    def include(self, includes: MembershipIncludes) -> 'ManageChannelMembers':
        super().include(includes)
        return self

    def build_path(self):
        return ManageChannelMembers.MANAGE_CHANNELS_MEMBERS_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def build_data(self):
        uuids_to_set = []
        uuids_to_remove = []

        for uuid in self._uuids_to_set:
            uuids_to_set.append(uuid.to_payload_dict())

        for uuid in self._uuids_to_remove:
            uuids_to_remove.append(uuid.to_payload_dict())

        payload = {
            "set": uuids_to_set,
            "delete": uuids_to_remove
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope) -> PNManageChannelMembersResult:
        return PNManageChannelMembersResult(envelope)

    def sync(self) -> PNManageChannelMembersResultEnvelope:
        return PNManageChannelMembersResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNManageChannelMembersOperation

    def name(self):
        return "Manage Channels Members"

    def http_method(self):
        return HttpMethod.PATCH
