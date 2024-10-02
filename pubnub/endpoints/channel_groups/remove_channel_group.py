from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_GROUP_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.channel_group import PNChannelGroupsRemoveGroupResult
from pubnub.models.consumer.common import PNStatus
from pubnub.structures import Envelope


class PNChannelGroupsRemoveGroupResultEnvelope(Envelope):
    result: PNChannelGroupsRemoveGroupResult
    status: PNStatus


class RemoveChannelGroup(Endpoint):
    # /v1/channel-registration/sub-key/<sub_key>/channel-group/<group_name>/remove
    REMOVE_PATH = "/v1/channel-registration/sub-key/%s/channel-group/%s/remove"

    def __init__(self, pubnub, channel_group: str = None):
        Endpoint.__init__(self, pubnub)
        self._channel_group = channel_group

    def channel_group(self, channel_group: str) -> 'RemoveChannelGroup':
        self._channel_group = channel_group
        return self

    def custom_params(self):
        return {}

    def build_path(self):
        return RemoveChannelGroup.REMOVE_PATH % (
            self.pubnub.config.subscribe_key, utils.url_encode(self._channel_group))

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

        if not isinstance(self._channel_group, str) or len(self._channel_group) == 0:
            raise PubNubException(pn_error=PNERR_GROUP_MISSING)

    def is_auth_required(self):
        return True

    def create_response(self, envelope):
        return PNChannelGroupsRemoveGroupResult()

    def sync(self) -> PNChannelGroupsRemoveGroupResultEnvelope:
        return PNChannelGroupsRemoveGroupResultEnvelope(super().sync())

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNRemoveGroupOperation

    def name(self):
        return "RemoveChannelGroup"
