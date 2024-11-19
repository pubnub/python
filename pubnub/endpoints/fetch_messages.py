import logging
from typing import List, Union

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.errors import PNERR_CHANNEL_MISSING, PNERR_HISTORY_MESSAGE_ACTIONS_MULTIPLE_CHANNELS
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.history import PNFetchMessagesResult
from pubnub.structures import Envelope

logger = logging.getLogger("pubnub")


class PNFetchMessagesResultEnvelope(Envelope):
    result: PNFetchMessagesResult
    status: PNStatus


class FetchMessages(Endpoint):
    FETCH_MESSAGES_PATH = "/v3/history/sub-key/%s/channel/%s"
    FETCH_MESSAGES_WITH_ACTIONS_PATH = "/v3/history-with-actions/sub-key/%s/channel/%s"

    SINGLE_CHANNEL_MAX_MESSAGES = 100
    DEFAULT_SINGLE_CHANNEL_MESSAGES = 100

    MULTIPLE_CHANNELS_MAX_MESSAGES = 25
    DEFAULT_MULTIPLE_CHANNELS_MESSAGES = 25

    MAX_MESSAGES_ACTIONS = 25
    DEFAULT_MESSAGES_ACTIONS = 25

    def __init__(self, pubnub, channels: Union[str, List[str]] = None, start: int = None, end: int = None,
                 count: int = None, include_meta: bool = None, include_message_actions: bool = None,
                 include_message_type: bool = None, include_uuid: bool = None, decrypt_messages: bool = False,
                 include_custom_message_type: bool = None):
        Endpoint.__init__(self, pubnub)
        self._channels = []
        if channels:
            utils.extend_list(self._channels, channels)
        self._start = start
        self._end = end
        self._count = count
        self._include_meta = include_meta
        self._include_message_actions = include_message_actions
        self._include_message_type = include_message_type
        self._include_uuid = include_uuid
        self._decrypt_messages = decrypt_messages
        self._include_custom_message_type = include_custom_message_type

    def channels(self, channels: Union[str, List[str]]) -> 'FetchMessages':
        utils.extend_list(self._channels, channels)
        return self

    def count(self, count: int) -> 'FetchMessages':
        assert isinstance(count, int)
        self._count = count
        return self

    def maximum_per_channel(self, maximum_per_channel) -> 'FetchMessages':
        return self.count(maximum_per_channel)

    def start(self, start: int) -> 'FetchMessages':
        assert isinstance(start, int)
        self._start = start
        return self

    def end(self, end: int) -> 'FetchMessages':
        assert isinstance(end, int)
        self._end = end
        return self

    def include_meta(self, include_meta: bool) -> 'FetchMessages':
        assert isinstance(include_meta, bool)
        self._include_meta = include_meta
        return self

    def include_message_actions(self, include_message_actions: bool) -> 'FetchMessages':
        assert isinstance(include_message_actions, bool)
        self._include_message_actions = include_message_actions
        return self

    def include_message_type(self, include_message_type: bool) -> 'FetchMessages':
        assert isinstance(include_message_type, bool)
        self._include_message_type = include_message_type
        return self

    def include_custom_message_type(self, include_custom_message_type: bool) -> 'FetchMessages':
        assert isinstance(include_custom_message_type, bool)
        self._include_custom_message_type = include_custom_message_type
        return self

    def include_uuid(self, include_uuid: bool) -> 'FetchMessages':
        assert isinstance(include_uuid, bool)
        self._include_uuid = include_uuid
        return self

    def decrypt_messages(self, decrypt: bool = True) -> 'FetchMessages':
        self._decrypt_messages = decrypt
        return self

    def custom_params(self):
        params = {'max': int(self._count)}

        if self._start is not None:
            params['start'] = str(self._start)

        if self._end is not None:
            params['end'] = str(self._end)

        if self._include_meta is not None:
            params['include_meta'] = "true" if self._include_meta else "false"

        if self._include_message_type is not None:
            params['include_message_type'] = "true" if self._include_message_type else "false"

        if self._include_custom_message_type is not None:
            params['include_custom_message_type'] = "true" if self._include_custom_message_type else "false"

        if self.include_message_actions and self._include_uuid is not None:
            params['include_uuid'] = "true" if self._include_uuid else "false"

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

        if not self._include_message_actions:
            if len(self._channels) == 1:
                if self._count is None or self._count < 1:
                    self._count = FetchMessages.DEFAULT_SINGLE_CHANNEL_MESSAGES
                    logger.info("count param defaulting to %d", self._count)
                elif self._count > FetchMessages.SINGLE_CHANNEL_MAX_MESSAGES:
                    self._count = FetchMessages.DEFAULT_SINGLE_CHANNEL_MESSAGES
                    logger.info("count param defaulting to %d", self._count)
            else:
                if self._count is None or self._count < 1:
                    self._count = FetchMessages.DEFAULT_MULTIPLE_CHANNELS_MESSAGES
                    logger.info("count param defaulting to %d", self._count)
                elif self._count > FetchMessages.MULTIPLE_CHANNELS_MAX_MESSAGES:
                    self._count = FetchMessages.DEFAULT_MULTIPLE_CHANNELS_MESSAGES
                    logger.info("count param defaulting to %d", self._count)
        else:
            if len(self._channels) > 1:
                raise PubNubException(pn_error=PNERR_HISTORY_MESSAGE_ACTIONS_MULTIPLE_CHANNELS)

            if self._count is None or self._count < 1 or\
                    self._count > FetchMessages.MAX_MESSAGES_ACTIONS:
                self._count = FetchMessages.DEFAULT_MESSAGES_ACTIONS
                logger.info("count param defaulting to %d", self._count)

    def create_response(self, envelope):  # pylint: disable=W0221
        return PNFetchMessagesResult.from_json(
            json_input=envelope,
            include_message_actions=self._include_message_actions,
            start_timetoken=self._start,
            end_timetoken=self._end,
            crypto_module=self.pubnub.crypto if self._decrypt_messages else None)

    def sync(self) -> PNFetchMessagesResultEnvelope:
        return PNFetchMessagesResultEnvelope(super().sync())

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNFetchMessagesOperation

    def name(self):
        return "Fetch messages"
