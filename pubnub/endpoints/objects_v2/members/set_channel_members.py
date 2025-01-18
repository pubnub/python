from typing import List
from pubnub import utils
from pubnub.endpoints.objects_v2.objects_endpoint import IncludeCapableEndpoint, ObjectsEndpoint, \
    IncludeCustomEndpoint, UUIDIncludeEndpoint, ChannelEndpoint, ListEndpoint
from pubnub.enums import PNOperationType
from pubnub.enums import HttpMethod
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.objects_v2.channel_members import PNUUID, PNSetChannelMembersResult
from pubnub.models.consumer.objects_v2.common import MemberIncludes
from pubnub.models.consumer.objects_v2.page import PNPage
from pubnub.structures import Envelope


class PNSetChannelMembersResultEnvelope(Envelope):
    result: PNSetChannelMembersResult
    status: PNStatus


class SetChannelMembers(ObjectsEndpoint, ChannelEndpoint, ListEndpoint, IncludeCustomEndpoint, IncludeCapableEndpoint,
                        UUIDIncludeEndpoint):
    SET_CHANNEL_MEMBERS_PATH = "/v2/objects/%s/channels/%s/uuids"

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

    def uuids(self, uuids) -> 'SetChannelMembers':
        utils.extend_list(self._uuids, uuids)
        return self

    def validate_specific_params(self):
        self._validate_channel()

    def include(self, includes: MemberIncludes) -> 'SetChannelMembers':
        """
        Include additional information in the members response.

        Parameters
        ----------
        includes : MemberIncludes
            The additional information to include in the member response.

        See Also
        --------
        pubnub.models.consumer.objects_v2.common.MemberIncludese : For details on the available includes.

        Returns
        -------
        self : SetChannelMembers
        """
        super().include(includes)
        return self

    def build_path(self):
        return SetChannelMembers.SET_CHANNEL_MEMBERS_PATH % (self.pubnub.config.subscribe_key, self._channel)

    def build_data(self):
        uuids_to_set = []

        for uuid in self._uuids:
            uuids_to_set.append(uuid.to_payload_dict())

        payload = {
            "set": uuids_to_set,
            "delete": []
        }
        return utils.write_value_as_string(payload)

    def create_response(self, envelope) -> PNSetChannelMembersResult:
        return PNSetChannelMembersResult(envelope)

    def sync(self) -> PNSetChannelMembersResultEnvelope:
        return PNSetChannelMembersResultEnvelope(super().sync())

    def operation_type(self):
        return PNOperationType.PNSetChannelMembersOperation

    def name(self):
        return "Set Channel Members"

    def http_method(self):
        return HttpMethod.PATCH
