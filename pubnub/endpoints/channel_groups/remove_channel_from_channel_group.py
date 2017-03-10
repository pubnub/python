import six

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_CHANNELS_MISSING, PNERR_GROUP_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.channel_group import PNChannelGroupsRemoveChannelResult


class RemoveChannelFromChannelGroup(Endpoint):
    # /v1/channel-registration/sub-key/<sub_key>/channel-group/<group_name>?remove=ch1,ch2
    REMOVE_PATH = "/v1/channel-registration/sub-key/%s/channel-group/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channels = []
        self._channel_group = None

    def channels(self, channels):
        if isinstance(channels, (list, tuple)):
            self._channels.extend(channels)
        else:
            self._channels.extend(utils.split_items(channels))

        return self

    def channel_group(self, channel_group):
        self._channel_group = channel_group

        return self

    def custom_params(self):
        return {'remove': utils.join_items(self._channels)}

    def build_path(self):
            return RemoveChannelFromChannelGroup.REMOVE_PATH % (
                self.pubnub.config.subscribe_key, utils.url_encode(self._channel_group))

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

        if len(self._channels) == 0:
            raise PubNubException(pn_error=PNERR_CHANNELS_MISSING)

        if not isinstance(self._channel_group, six.string_types)\
                or len(self._channel_group) == 0:
            raise PubNubException(pn_error=PNERR_GROUP_MISSING)

    def is_auth_required(self):
        return True

    def create_response(self, envelope):
        return PNChannelGroupsRemoveChannelResult()

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNRemoveChannelsFromGroupOperation

    def name(self):
        return "RemoveChannelToChannelGroup"
