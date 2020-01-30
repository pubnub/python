import six

from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.message_actions import PNGetMessageActionsResult, PNMessageAction
from pubnub.enums import HttpMethod, PNOperationType


class GetMessageActions(Endpoint):
    GET_MESSAGE_ACTIONS_PATH = '/v1/message-actions/%s/channel/%s'
    MAX_LIMIT = 100

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = None
        self._start = None
        self._end = None
        self._limit = GetMessageActions.MAX_LIMIT

    def channel(self, channel):
        self._channel = str(channel)
        return self

    def start(self, start):
        assert isinstance(start, six.string_types)
        self._start = start
        return self

    def end(self, end):
        assert isinstance(end, six.string_types)
        self._end = end
        return self

    def limit(self, limit):
        assert isinstance(limit, six.integer_types)
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

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNGetMessageActions

    def name(self):
        return 'Get message actions'
