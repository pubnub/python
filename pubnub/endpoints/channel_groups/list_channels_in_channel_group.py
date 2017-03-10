import six

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_GROUP_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.channel_group import PNChannelGroupsListResult


class ListChannelsInChannelGroup(Endpoint):
    # /v1/channel-registration/sub-key/<sub_key>/channel-group/<group_name>
    LIST_PATH = "/v1/channel-registration/sub-key/%s/channel-group/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel_group = None

    def channel_group(self, channel_group):
        self._channel_group = channel_group

        return self

    def custom_params(self):
        return {}

    def build_path(self):
            return ListChannelsInChannelGroup.LIST_PATH % (
                self.pubnub.config.subscribe_key, utils.url_encode(self._channel_group))

    def http_method(self):
        return HttpMethod.GET

    def validate_params(self):
        self.validate_subscribe_key()

        if not isinstance(self._channel_group, six.string_types)\
                or len(self._channel_group) == 0:
            raise PubNubException(pn_error=PNERR_GROUP_MISSING)

    def create_response(self, envelope):
        if 'payload' in envelope and 'channels' in envelope['payload']:
            return PNChannelGroupsListResult(envelope['payload']['channels'])
        else:
            return PNChannelGroupsListResult([])

    def is_auth_required(self):
        return True

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNChannelsForGroupOperation

    def name(self):
        return "ListChannelsInChannelGroup"
