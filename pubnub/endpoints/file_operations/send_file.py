from pubnub.endpoints.file_operations.file_based_endpoint import FileOperationEndpoint

from pubnub.crypto import PubNubFileCrypto
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.models.consumer.file import PNSendFileResult
from pubnub.endpoints.file_operations.publish_file_message import PublishFileMessage
from pubnub.endpoints.file_operations.fetch_upload_details import FetchFileUploadS3Data
from pubnub.endpoints.mixins import TimeTokenOverrideMixin
from warnings import warn


class SendFileNative(FileOperationEndpoint, TimeTokenOverrideMixin):
    def __init__(self, pubnub):
        super(SendFileNative, self).__init__(pubnub)
        self._file_name = None
        self._pubnub = pubnub
        self._file_upload_envelope = None
        self._message = None
        self._should_store = None
        self._ttl = 0
        self._meta = None
        self._cipher_key = None
        self._file_object = None
        self._replicate = None
        self._ptto = None
        self._custom_message_type = None

    def file_object(self, fd):
        self._file_object = fd
        return self

    def custom_message_type(self, custom_message_type: str):
        self._custom_message_type = custom_message_type
        return self

    def build_params_callback(self):
        return lambda a: {}

    def build_path(self):
        return self._file_upload_envelope.result.data["url"]

    def encrypt_payload(self):
        try:
            payload = self._file_object.read()
        except AttributeError:
            payload = self._file_object
        if self._cipher_key:
            return PubNubFileCrypto(self._pubnub.config).encrypt(self._cipher_key, payload)
        elif self._pubnub.config.cipher_key:
            return self._pubnub.crypto.encrypt_file(payload)
        else:
            return self._file_object

    def build_file_upload_request(self):
        file = self.encrypt_payload()
        multipart_body = {}
        for form_field in self._file_upload_envelope.result.data["form_fields"]:
            multipart_body[form_field["key"]] = (None, form_field["value"])

        multipart_body["file"] = (self._file_name, file, None)

        return multipart_body

    def http_method(self):
        return HttpMethod.POST

    def use_compression(self, compress=True):
        self._use_compression = bool(compress)
        return self

    def is_compressable(self):
        return True

    def custom_params(self):
        return {}

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()
        self.validate_file_object()
        self.validate_file_name()

    def use_base_path(self):
        return False

    def non_json_response(self):
        return True

    def is_auth_required(self):
        return False

    def should_store(self, should_store):
        self._should_store = bool(should_store)
        return self

    def ttl(self, ttl):
        self._ttl = ttl
        return self

    def meta(self, meta):
        self._meta = meta
        return self

    def message(self, message):
        self._message = message
        return self

    def file_name(self, file_name):
        self._file_name = file_name
        return self

    def cipher_key(self, cipher_key):
        if cipher_key:
            warn('Deprecated: Usage of local cipher_keys is discouraged. Use pnconfiguration.cipher_key instead')
            self._cipher_key = cipher_key
        return self

    def create_response(self, envelope, data=None):
        return PNSendFileResult(envelope, self._file_upload_envelope)

    def operation_type(self):
        return PNOperationType.PNSendFileAction

    def request_headers(self):
        return {}

    def name(self):
        return "Send file to S3"

    def sync(self):
        self._file_upload_envelope = FetchFileUploadS3Data(self._pubnub) \
            .channel(self._channel) \
            .file_name(self._file_name).sync()

        response_envelope = super(SendFileNative, self).sync()

        publish_file_response = PublishFileMessage(self._pubnub) \
            .channel(self._channel) \
            .meta(self._meta) \
            .message(self._message) \
            .file_id(response_envelope.result.file_id) \
            .file_name(response_envelope.result.name) \
            .should_store(self._should_store) \
            .ttl(self._ttl) \
            .replicate(self._replicate) \
            .ptto(self._ptto) \
            .custom_message_type(self._custom_message_type) \
            .cipher_key(self._cipher_key).sync()

        response_envelope.result.timestamp = publish_file_response.result.timestamp
        return response_envelope

    def pn_async(self, callback):
        self._pubnub.get_request_handler().async_file_based_operation(self.sync, callback, "File Download")
