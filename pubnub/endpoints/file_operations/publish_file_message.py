from pubnub.endpoints.file_operations.file_based_endpoint import FileOperationEndpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub import utils
from pubnub.models.consumer.file import PNPublishFileMessageResult
from pubnub.endpoints.mixins import TimeTokenOverrideMixin
from pubnub.models.consumer.message_type import PNMessageType
from typing import Union


class PublishFileMessage(FileOperationEndpoint, TimeTokenOverrideMixin):
    PUBLISH_FILE_MESSAGE = "/v1/files/publish-file/%s/%s/0/%s/0/%s"

    def __init__(self, pubnub):
        super(PublishFileMessage, self).__init__(pubnub)
        self._file_id = None
        self._file_name = None
        self._pubnub = pubnub
        self._message = None
        self._should_store = None
        self._ttl = 0
        self._meta = None
        self._cipher_key = None
        self._replicate = None
        self._ptto = None
        self._message_type = None
        self._space_id = None

    def meta(self, meta):
        self._meta = meta
        return self

    def should_store(self, should_store):
        self._should_store = bool(should_store)
        return self

    def cipher_key(self, cipher_key):
        self._cipher_key = cipher_key
        return self

    def message(self, message):
        self._message = message
        return self

    def file_id(self, file_id):
        self._file_id = file_id
        return self

    def ttl(self, ttl):
        self._ttl = ttl
        return self

    def file_name(self, file_name):
        self._file_name = file_name
        return self

    def message_type(self, message_type: Union[PNMessageType, str]):
        self._message_type = message_type
        return self

    def space_id(self, space_id):
        self._space_id = str(space_id)
        return self

    def _encrypt_message(self, message):
        if self._cipher_key or self._pubnub.config.cipher_key:
            return self._pubnub.config.crypto.encrypt(
                self._cipher_key or self._pubnub.config.cipher_key,
                utils.write_value_as_string(message)
            )
        else:
            return message

    def _build_message(self):
        message = {
            "message": self._message,
            "file": {
                "id": self._file_id,
                "name": self._file_name
            }
        }
        return self._encrypt_message(message)

    def build_path(self):
        message = self._build_message()
        return PublishFileMessage.PUBLISH_FILE_MESSAGE % (
            self.pubnub.config.publish_key,
            self.pubnub.config.subscribe_key,
            utils.url_encode(self._channel),
            utils.url_write(message)
        )

    def http_method(self):
        return HttpMethod.GET

    def custom_params(self):
        params = TimeTokenOverrideMixin.custom_params(self)
        params.update({
            "meta": utils.url_write(self._meta),
            "ttl": self._ttl,
            "store": 1 if self._should_store else 0
        })
        if self._message_type is not None:
            params['type'] = str(self._message_type)

        if self._space_id is not None:
            params['space-id'] = str(self._space_id)

        return params

    def is_auth_required(self):
        return True

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()
        self.validate_file_name()
        self.validate_file_id()

    def create_response(self, envelope):
        return PNPublishFileMessageResult(envelope)

    def operation_type(self):
        return PNOperationType.PNSendFileAction

    def name(self):
        return "Sending file upload notification"
