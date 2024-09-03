from typing import Optional
from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.exceptions import PubNubException
from pubnub.errors import PNERR_MESSAGE_MISSING
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNFireResult
from pubnub.structures import Envelope


class PNFireResultEnvelope(Envelope):
    result: PNFireResult
    status: PNStatus


class Fire(Endpoint):
    # /publish/<pub_key>/<sub_key>/<signature>/<channel>/<callback>/<message>[?argument(s)]
    FIRE_GET_PATH = "/publish/%s/%s/0/%s/%s/%s"
    FIRE_POST_PATH = "/publish/%s/%s/0/%s/%s"

    _channel: str
    _message: any
    _use_post: Optional[bool]
    _meta: Optional[any]

    def __init__(self, pubnub, channel: Optional[str] = None, message: Optional[any] = None,
                 use_post: Optional[bool] = None, meta: Optional[any] = None):
        Endpoint.__init__(self, pubnub)
        self._channel = channel
        self._message = message
        self._use_post = use_post
        self._meta = meta

    def channel(self, channel: str) -> 'Fire':
        self._channel = str(channel)
        return self

    def message(self, message) -> 'Fire':
        self._message = message
        return self

    def use_post(self, use_post) -> 'Fire':
        self._use_post = bool(use_post)
        return self

    def is_compressable(self) -> bool:
        return True

    def use_compression(self, compress=True) -> 'Fire':
        self._use_compression = bool(compress)
        return self

    def meta(self, meta) -> 'Fire':
        self._meta = meta
        return self

    def build_data(self):
        if self._use_post is True:
            stringified_message = utils.write_value_as_string(self._message)
            if self.pubnub.config.crypto_module:
                stringified_message = '"' + self.pubnub.config.crypto_module.encrypt(stringified_message) + '"'
            elif self.pubnub.config.cipher_key is not None:  # The legacy way
                stringified_message = '"' + self.pubnub.config.crypto.encrypt(
                    self.pubnub.config.cipher_key,
                    stringified_message) + '"'

            return stringified_message
        else:
            return None

    def custom_params(self):
        params = {}
        if self._meta is not None:
            params['meta'] = utils.write_value_as_string(self._meta)
        params["store"] = "0"
        params["norep"] = "1"
        if self.pubnub.config.auth_key is not None:
            params["auth"] = utils.url_encode(self.pubnub.config.auth_key)
        return params

    def build_path(self):
        if self._use_post:
            return Fire.FIRE_POST_PATH % (self.pubnub.config.publish_key,
                                          self.pubnub.config.subscribe_key,
                                          utils.url_encode(self._channel), 0)
        else:
            stringified_message = utils.write_value_as_string(self._message)
            if self.pubnub.config.crypto_module:
                stringified_message = '"' + self.pubnub.config.crypto_module.encrypt(stringified_message) + '"'
            elif self.pubnub.config.cipher_key is not None:  # The legacy way
                stringified_message = '"' + self.pubnub.config.crypto.encrypt(
                    self.pubnub.config.cipher_key,
                    stringified_message) + '"'

            stringified_message = utils.url_encode(stringified_message)

            return Fire.FIRE_GET_PATH % (self.pubnub.config.publish_key,
                                         self.pubnub.config.subscribe_key,
                                         utils.url_encode(self._channel), 0, stringified_message)

    def http_method(self):
        if self._use_post is True:
            return HttpMethod.POST
        else:
            return HttpMethod.GET

    def validate_params(self):
        self.validate_channel()

        if self._message is None:
            raise PubNubException(pn_error=PNERR_MESSAGE_MISSING)

        self.validate_subscribe_key()
        self.validate_publish_key()

    def create_response(self, envelope) -> PNFireResult:
        """
        :param envelope: an already serialized json response
        :return:
        """
        if envelope is None:
            return None

        timetoken = int(envelope[2])

        res = PNFireResult(envelope, timetoken)

        return res

    def sync(self) -> PNFireResultEnvelope:
        return PNFireResultEnvelope(super().sync())

    def is_auth_required(self):
        return True

    def affected_channels(self):
        return None

    def affected_channels_groups(self):
        return None

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout

    def operation_type(self):
        return PNOperationType.PNFireOperation

    def name(self):
        return "Fire"
