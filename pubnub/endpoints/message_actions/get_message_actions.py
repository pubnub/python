from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.message_actions import PNGetMessageActionsResult, PNMessageAction
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.structures import Envelope


class PNGetMessageActionsResultEnvelope(Envelope):
    result: PNGetMessageActionsResult
    status: PNStatus


class GetMessageActions(Endpoint):
    GET_MESSAGE_ACTIONS_PATH = '/v1/message-actions/%s/channel/%s'
    MAX_LIMIT = 100

    def __init__(self, pubnub, channel: str = None, start: str = None, end: str = None, limit: str = None):
        Endpoint.__init__(self, pubnub)
        self._channel = channel
        self._start = start
        self._end = end
        self._limit = limit or GetMessageActions.MAX_LIMIT

    def channel(self, channel: str) -> 'GetMessageActions':
        self._channel = str(channel)
        return self

    def start(self, start: str) -> 'GetMessageActions':
        assert isinstance(start, str)
        self._start = start
        return self

    def end(self, end: str) -> 'GetMessageActions':
        assert isinstance(end, str)
        self._end = end
        return self

    def limit(self, limit: str) -> 'GetMessageActions':
        assert isinstance(limit, str)
        self._limit = limit
        return self

    def custom_params(self):
        params = {}

        if self._start is not None:
            params['start'] = self._start

        if self._end is not None and self._start is None:
            params['end'] = self._end

        if self._limit != GetMessageActions.MAX_LIMIT:
            params['limit'] = self._limit

        return params

    def build_path(self):
        return GetMessageActions.GET_MESSAGE_ACTIONS_PATH % (
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel)
        )

    def http_method(self):
        return HttpMethod.GET

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()

    def create_response(self, envelope):   # pylint: disable=W0221
        result = envelope
        result['actions'] = []
        for action in result['data']:
            result['actions'].append(PNMessageAction(action))

        return PNGetMessageActionsResult(result)

    def sync(self) -> PNGetMessageActionsResultEnvelope:
        return PNGetMessageActionsResultEnvelope(super().sync())

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNGetMessageActions

    def name(self):
        return 'Get message actions'
