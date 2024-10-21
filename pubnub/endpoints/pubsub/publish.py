from typing import Optional
from pubnub import utils
from pubnub.endpoints.endpoint import Endpoint
from pubnub.errors import PNERR_MESSAGE_MISSING
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.endpoints.mixins import TimeTokenOverrideMixin
from pubnub.structures import Envelope


class PNPublishResultEnvelope(Envelope):
    result: PNPublishResult
    status: PNStatus


class Publish(Endpoint, TimeTokenOverrideMixin):
    # /publish/<pub_key>/<sub_key>/<signature>/<channel>/<callback>/<message>[?argument(s)]
    PUBLISH_GET_PATH = "/publish/%s/%s/0/%s/%s/%s"
    PUBLISH_POST_PATH = "/publish/%s/%s/0/%s/%s"

    _channel: str
    _message: any
    _should_store: Optional[bool]
    _use_post: Optional[bool]
    _meta: Optional[any]
    _replicate: Optional[bool]
    _ptto: Optional[int]
    _ttl: Optional[int]

    def __init__(self, pubnub, channel: str = None, message: any = None, should_store: Optional[bool] = None,
                 use_post: Optional[bool] = None, meta: Optional[any] = None, replicate: Optional[bool] = None,
                 ptto: Optional[int] = None, ttl: Optional[int] = None, custom_message_type: Optional[str] = None):

        super(Publish, self).__init__(pubnub)
        self._channel = channel
        self._message = message
        self._should_store = should_store
        self._use_post = use_post
        self._meta = meta
        self._custom_message_type = custom_message_type
        self._replicate = replicate
        self._ptto = ptto
        self._ttl = ttl

    def channel(self, channel: str) -> 'Publish':
        self._channel = str(channel)
        return self

    def message(self, message: any) -> 'Publish':
        self._message = message
        return self

    def use_post(self, use_post: bool) -> 'Publish':
        self._use_post = bool(use_post)
        return self

    def use_compression(self, compress: bool = True) -> 'Publish':
        self._use_compression = bool(compress)
        return self

    def is_compressable(self) -> bool:
        return True

    def should_store(self, should_store: bool) -> 'Publish':
        self._should_store = bool(should_store)
        return self

    def meta(self, meta: any) -> 'Publish':
        self._meta = meta
        return self

    def custom_message_type(self, custom_message_type: str) -> 'Publish':
        self._custom_message_type = custom_message_type
        return self

    def ttl(self, ttl: int) -> 'Publish':
        self._ttl = ttl
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

    def encoded_params(self):
        if self._meta:
            return {
                "meta": utils.url_write(self._meta)
            }
        else:
            return {}

    def custom_params(self):
        params = TimeTokenOverrideMixin.custom_params(self)

        if self._ttl:
            params['ttl'] = self._ttl

        if self._meta:
            params['meta'] = utils.write_value_as_string(self._meta)

        if self._custom_message_type:
            params['custom_message_type'] = utils.url_encode(self._custom_message_type)

        if self._should_store is not None:
            if self._should_store:
                params["store"] = "1"
            else:
                params["store"] = "0"

        # REVIEW: should auth key be assigned here?
        if self.pubnub.config.auth_key is not None:
            params["auth"] = utils.url_encode(self.pubnub.config.auth_key)

        return params

    def build_path(self):
        if self._use_post:
            return Publish.PUBLISH_POST_PATH % (self.pubnub.config.publish_key,
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

            return Publish.PUBLISH_GET_PATH % (self.pubnub.config.publish_key,
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

    def create_response(self, envelope):
        """
        :param envelope: an already serialized json response
        :return:
        """
        if envelope is None:
            return None

        timetoken = int(envelope[2])

        res = PNPublishResult(envelope, timetoken)

        return res

    def sync(self) -> PNPublishResultEnvelope:
        return PNPublishResultEnvelope(super().sync())

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
        return PNOperationType.PNPublishOperation

    def name(self):
        return "Publish"
