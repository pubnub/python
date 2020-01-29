from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_MESSAGE_ACTION_VALUE_MISSING, PNERR_MESSAGE_ACTION_TYPE_MISSING, \
    PNERR_MESSAGE_TIMETOKEN_MISSING, PNERR_MESSAGE_ACTION_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.message_actions import PNAddMessageActionResult


class AddMessageAction(Endpoint):
    ADD_MESSAGE_ACTION_PATH = "/v1/message-actions/%s/channel/%s/message/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = None
        self._message_action = None

    def channel(self, channel):
        self._channel = str(channel)
        return self

    def message_action(self, message_action):
        self._message_action = message_action
        return self

    def custom_params(self):
        return {}

    def build_data(self):
        params = {
            'type': self._message_action.type,
            'value': self._message_action.value
        }

        return utils.write_value_as_string(params)

    def build_path(self):
        return AddMessageAction.ADD_MESSAGE_ACTION_PATH % (
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel),
            self._message_action.message_timetoken
        )

    def http_method(self):
        return HttpMethod.POST

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()
        self.validate_message_action()

    def create_response(self, envelope):  # pylint: disable=W0221
        return PNAddMessageActionResult(envelope['data'])

    def is_auth_required(self):
        return True

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNAddMessageAction

    def name(self):
        return "Add message action"

    def validate_message_action(self):
        if self._message_action is None:
            raise PubNubException(pn_error=PNERR_MESSAGE_ACTION_MISSING)

        if self._message_action.message_timetoken is None:
            raise PubNubException(pn_error=PNERR_MESSAGE_TIMETOKEN_MISSING)

        if self._message_action.type is None or len(self._message_action.type) == 0:
            raise PubNubException(pn_error=PNERR_MESSAGE_ACTION_TYPE_MISSING)

        if self._message_action.value is None or len(self._message_action.value) == 0:
            raise PubNubException(pn_error=PNERR_MESSAGE_ACTION_VALUE_MISSING)
