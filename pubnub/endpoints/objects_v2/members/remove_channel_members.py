from typing import List
from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import IncludeCapableEndpoint, ObjectsEndpoint, ChannelEndpoint, \
    ListEndpoint, IncludeCustomEndpoint, UUIDIncludeEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel_members import PNUUID, PNRemoveChannelMembersResult
from pubnub.models.consumer.objects_v2.common import MemberIncludes
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.structures import Envelope


class PNRemoveChannelMembersResultEnvelope(Envelope):
    result: PNRemoveChannelMembersResult
    status: PNStatus


class RemoveChannelMembers(ObjectsEndpoint, ChannelEndpoint, ListEndpoint, IncludeCustomEndpoint,
                           UUIDIncludeEndpoint, IncludeCapableEndpoint):
    REMOVE_CHANNEL_MEMBERS_PATH = "/v2/objects/%s/channels/%s/uuids"

    def __init__(self, pubnub, channel: str = None, uuids: List[PNUUID] = None, include_custom: bool = None,
                 limit: int = None, filter: str = None, include_total_count: bool = None, sort_keys: list = None,
                 page: PNPage = None, include: MemberIncludes = None):
        ObjectsEndpoint.__init__(self, pubnub)
        IncludeCapableEndpoint.__init__(self, include)
        ListEndpoint.__init__(self, limit=limit, filter=filter, include_total_count=include_total_count,
                              sort_keys=sort_keys, page=page)
        ChannelEndpoint.__init__(self, channel=channel)
        IncludeCustomEndpoint.__init__(self, include_custom=include_custom)
        UUIDIncludeEndpoint.__init__(self)

        self._uuids = []
        if uuids:
            utils.extend_list(self._uuids, uuids)

    def uuids(self, uuids: List[str]) -> 'RemoveChannelMembers':
        utils.extend_list(self._uuids, uuids)
        return self

    def build_path(self):
        return RemoveChannelMembers.REMOVE_CHANNEL_MEMBERS_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def build_data(self):
        uuids_to_delete = []

        for uuid in self._uuids:
            uuids_to_delete.append(uuid.to_payload_dict())

        payload = {
            "set": [],
            "delete": uuids_to_delete
        }
        return utils.write_value_as_string(payload)

    def validate_specific_params(self):
        self._validate_channel()

    def create_response(self, envelope) -> PNRemoveChannelMembersResult:
        return PNRemoveChannelMembersResult(envelope)

    def sync(self) -> PNRemoveChannelMembersResultEnvelope:
        return PNRemoveChannelMembersResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNRemoveChannelMembersOperation

    def name(self):
        return "Remove Channel Members"

    def http_method(self):
        return HttpMethod.PATCH
