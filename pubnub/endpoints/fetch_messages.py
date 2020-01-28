import logging

import six

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.errors import PNERR_CHANNEL_MISSING, PNERR_HISTORY_MESSAGE_ACTIONS_MULTIPLE_CHANNELS
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.history import PNFetchMessagesResult

logger = logging.getLogger("pubnub")


class FetchMessages(Endpoint):
    FETCH_MESSAGES_PATH = "/v3/history/sub-key/%s/channel/%s"
    FETCH_MESSAGES_WITH_ACTIONS_PATH = "/v3/history-with-actions/sub-key/%s/channel/%s"

    DEFAULT_MESSAGES = 100
    MAX_MESSAGES = 25
    MAX_MESSAGES_ACTIONS = 100

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channels = []
        self._start = None
        self._end = None
        self._maximum_per_channel = None
        self._include_meta = None
        self._include_message_actions = None

    def channels(self, channels):
        utils.extend_list(self._channels, channels)
        return self

    def maximum_per_channel(self, maximum_per_channel):
        assert isinstance(maximum_per_channel, six.integer_types)
        self._maximum_per_channel = maximum_per_channel
        return self

    def start(self, start):
        assert isinstance(start, six.integer_types)
        self._start = start
        return self

    def end(self, end):
        assert isinstance(end, six.integer_types)
        self._end = end
        return self

    def include_meta(self, include_meta):
        assert isinstance(include_meta, bool)
        self._include_meta = include_meta
        return self

    def include_message_actions(self, include_message_actions):
        assert isinstance(include_message_actions, bool)
        self._include_message_actions = include_message_actions
        return self

    def custom_params(self):
        params = {'max': str(self._maximum_per_channel)}

        if self._start is not None:
            params['start'] = str(self._start)

        if self._end is not None:
            params['end'] = str(self._end)

        if self._include_meta is not None:
            params['include_meta'] = "true" if self._include_meta else "false"

        return params

    def build_path(self):
        if self._include_message_actions is False:
            return FetchMessages.FETCH_MESSAGES_PATH % (
                self.pubnub.config.subscribe_key,
                utils.join_channels(self._channels)
            )
        else:
            return FetchMessages.FETCH_MESSAGES_WITH_ACTIONS_PATH % (
                self.pubnub.config.subscribe_key,
                utils.url_encode(self._channels[0])
            )

    def http_method(self):
        return HttpMethod.GET

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()

        if self._channels is None or len(self._channels) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_MISSING)

        if self._include_meta is None:
            self._include_meta = False

        if self._include_message_actions is None:
            self._include_message_actions = False

        if self._include_message_actions is False:
            if self._maximum_per_channel is None or self._maximum_per_channel < FetchMessages.DEFAULT_MESSAGES:
                self._maximum_per_channel = FetchMessages.DEFAULT_MESSAGES
                logger.info("maximum_per_channel param defaulting to %d", FetchMessages.DEFAULT_MESSAGES)
            elif self._maximum_per_channel > FetchMessages.MAX_MESSAGES:
                self._maximum_per_channel = FetchMessages.MAX_MESSAGES
                logger.info("maximum_per_channel param defaulting to %d", FetchMessages.DEFAULT_MESSAGES)
        else:
            if len(self._channels) > 1:
                raise PubNubException(pn_error=PNERR_HISTORY_MESSAGE_ACTIONS_MULTIPLE_CHANNELS)

            if self._maximum_per_channel is None or self._maximum_per_channel < 1 or\
                    self._maximum_per_channel > FetchMessages.MAX_MESSAGES_ACTIONS:
                self._maximum_per_channel = FetchMessages.MAX_MESSAGES_ACTIONS
                logger.info("maximum_per_channel param defaulting to %d", FetchMessages.DEFAULT_MESSAGES)

    def create_response(self, envelope):  # pylint: disable=W0221
        return PNFetchMessagesResult.from_json(
            json_input=envelope,
            include_message_actions=self._include_message_actions,
            start_timetoken=self._start,
            end_timetoken=self._end)

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNFetchMessagesOperation

    def name(self):
        return "Fetch messages"
