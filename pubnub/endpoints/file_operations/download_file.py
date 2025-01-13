from pubnub.endpoints.file_operations.file_based_endpoint import FileOperationEndpoint
from pubnub.enums import HttpMethod, PNOperationType
from pubnub.crypto import PubNubFileCrypto
from pubnub.models.consumer.file import PNDownloadFileResult
from pubnub.endpoints.file_operations.get_file_url import GetFileDownloadUrl
from warnings import warn
from urllib.parse import urlparse, parse_qs


class DownloadFileNative(FileOperationEndpoint):
    def __init__(self, pubnub):
        FileOperationEndpoint.__init__(self, pubnub)
        self._file_id = None
        self._file_name = None
        self._pubnub = pubnub
        self._download_data = None
        self._cipher_key = None

    def cipher_key(self, cipher_key):
        warn('Deprecated: Usage of local cipher_keys is discouraged. Use pnconfiguration.cipher_key instead')
        self._cipher_key = cipher_key
        return self

    def build_path(self):
        return self._download_data.result.file_url

    def http_method(self):
        return HttpMethod.GET

    def is_auth_required(self):
        return False

    def custom_params(self):
        return {}

    def file_id(self, file_id):
        self._file_id = file_id
        return self

    def file_name(self, file_name):
        self._file_name = file_name
        return self

    def decrypt_payload(self, data):
        if self._cipher_key:
            return PubNubFileCrypto(self._pubnub.config).decrypt(self._cipher_key, data)
        else:
            return self._pubnub.crypto.decrypt_file(data)

    def validate_params(self):
        self.validate_subscribe_key()
        self.validate_channel()
        self.validate_file_name()
        self.validate_file_id()

    def create_response(self, envelope):
        if self._cipher_key or self._pubnub.config.cipher_key:
            return PNDownloadFileResult(self.decrypt_payload(envelope.content))
        else:
            return PNDownloadFileResult(envelope.content)

    def non_json_response(self):
        return True

    def operation_type(self):
        return PNOperationType.PNDownloadFileAction

    def use_base_path(self):
        return False

    def build_params_callback(self):
        params = parse_qs(urlparse(self._download_data.result.file_url).query)
        return lambda a: {key: str(params[key][0]) for key in params.keys()}

    def name(self):
        return "Downloading file"

    def sync(self):
        self._download_data = GetFileDownloadUrl(self._pubnub)\
            .channel(self._channel)\
            .file_name(self._file_name)\
            .file_id(self._file_id)\
            .sync()

        return super(DownloadFileNative, self).sync()

    def pn_async(self, callback):
        self._pubnub.get_request_handler().async_file_based_operation(self.sync, callback, "File Download")
