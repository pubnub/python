from typing import Optional
from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.signal import PNSignalResult
from pubnub.structures import Envelope


class SignalResultEnvelope(Envelope):
    result: PNSignalResult
    status: PNStatus


class Signal(Endpoint):
    SIGNAL_PATH = '/signal/%s/%s/0/%s/0/%s'

    _channel: str
    _message: any

    def __init__(self, pubnub, channel: str = None, message: any = None, custom_message_type: Optional[str] = None):
        Endpoint.__init__(self, pubnub)
        self._channel = channel
        self._message = message
        self._custom_message_type = custom_message_type

    def channel(self, channel) -> 'Signal':
        self._channel = str(channel)
        return self

    def message(self, message) -> 'Signal':
        self._message = message
        return self

    def custom_message_type(self, custom_message_type: str) -> 'Signal':
        self._custom_message_type = custom_message_type
        return self

    def build_path(self):
        stringified_message = utils.write_value_as_string(self._message)
        msg = utils.url_encode(stringified_message)
        return Signal.SIGNAL_PATH % (
            self.pubnub.config.publish_key, self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel), msg
        )

    def custom_params(self):
        params = {}
        if self._custom_message_type:
            params['custom_message_type'] = utils.url_encode(self._custom_message_type)

        return params

    def http_method(self):
        return HttpMethod.GET

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_publish_key()
        self.validate_channel()

    def create_response(self, result):  # pylint: disable=W0221
        return PNSignalResult(result)

    def sync(self) -> SignalResultEnvelope:
        return SignalResultEnvelope(super().sync())

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNSignalOperation

    def name(self):
        return "Signal"
