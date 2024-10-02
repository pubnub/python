from typing import List, Union
from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_CHANNELS_MISSING, PNERR_GROUP_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.channel_group import PNChannelGroupsAddChannelResult
from pubnub.models.consumer.common import PNStatus
from pubnub.structures import Envelope


class PNChannelGroupsAddChannelResultEnvelope(Envelope):
    result: PNChannelGroupsAddChannelResult
    status: PNStatus


class AddChannelToChannelGroup(Endpoint):
    # /v1/channel-registration/sub-key/<sub_key>/channel-group/<group_name>?add=ch1,ch2
    ADD_PATH = "/v1/channel-registration/sub-key/%s/channel-group/%s"

    def __init__(self, pubnub, channels: Union[str, List[str]] = None, channel_group: str = None):
        Endpoint.__init__(self, pubnub)
        self._channels = []
        if channels:
            utils.extend_list(self._channels, channels)
        self._channel_group = channel_group

    def channels(self, channels) -> 'AddChannelToChannelGroup':
        utils.extend_list(self._channels, channels)
        return self

    def channel_group(self, channel_group: str) -> 'AddChannelToChannelGroup':
        self._channel_group = channel_group
        return self

    def custom_params(self):
        return {'add': utils.join_items(self._channels)}

    def build_path(self):
        return AddChannelToChannelGroup.ADD_PATH % (
            self.pubnub.config.subscribe_key, utils.url_encode(self._channel_group))

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

        if len(self._channels) == 0:
            raise PubNubException(pn_error=PNERR_CHANNELS_MISSING)

        if not isinstance(self._channel_group, str) or len(self._channel_group) == 0:
            raise PubNubException(pn_error=PNERR_GROUP_MISSING)

    def is_auth_required(self):
        return True

    def create_response(self, envelope) -> PNChannelGroupsAddChannelResult:
        return PNChannelGroupsAddChannelResult()

    def sync(self) -> PNChannelGroupsAddChannelResultEnvelope:
        return PNChannelGroupsAddChannelResultEnvelope(super().sync())

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNAddChannelsToGroupOperation

    def name(self):
        return "AddChannelToChannelGroup"
