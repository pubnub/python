from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_MESSAGE_TIMETOKEN_MISSING, PNERR_MESSAGE_ACTION_TIMETOKEN_MISSING
from pubnub.exceptions import PubNubException
from pubnub.enums import HttpMethod, PNOperationType


class RemoveMessageAction(Endpoint):
    REMOVE_MESSAGE_ACTION_PATH = "/v1/message-actions/%s/channel/%s/message/%s/action/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = None
        self._message_timetoken = None
        self._action_timetoken = None

    def channel(self, channel):
        self._channel = str(channel)
        return self

    def message_timetoken(self, message_timetoken):
        self._message_timetoken = message_timetoken
        return self

    def action_timetoken(self, action_timetoken):
        self._action_timetoken = action_timetoken
        return self

    def custom_params(self):
        return {}

    def build_data(self):
        return None

    def build_path(self):
        return RemoveMessageAction.REMOVE_MESSAGE_ACTION_PATH % (
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel),
            self._message_timetoken,
            self._action_timetoken
        )

    def http_method(self):
        return HttpMethod.DELETE

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()
        self.validate_timetokens()

    def create_response(self, envelope):  # pylint: disable=W0221
        return {}

    def is_auth_required(self):
        return True

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNDeleteMessageAction

    def name(self):
        return "Remove message action"

    def validate_timetokens(self):

        if self._message_timetoken is None:
            raise PubNubException(pn_error=PNERR_MESSAGE_TIMETOKEN_MISSING)

        if self._action_timetoken is None:
            raise PubNubException(pn_error=PNERR_MESSAGE_ACTION_TIMETOKEN_MISSING)
