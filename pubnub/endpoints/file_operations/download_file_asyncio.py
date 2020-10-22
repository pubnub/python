from pubnub.models.consumer.file import PNDownloadFileResult
from pubnub.endpoints.file_operations.download_file import DownloadFileNative
from pubnub.endpoints.file_operations.get_file_url import GetFileDownloadUrl


class DownloadFileAsyncio(DownloadFileNative):
    def create_response(self, envelope, data=None):
        if self._cipher_key or self._pubnub.config.cipher_key:
            data = self.decrypt_payload(data)
        return PNDownloadFileResult(data)

    def future(self):
        self._download_data = yield from GetFileDownloadUrl(self._pubnub)\
            .channel(self._channel)\
            .file_name(self._file_name)\
            .file_id(self._file_id)\
            .future()

        downloaded_file = yield from super(DownloadFileAsyncio, self).future()
        return downloaded_file

    def result(self):
        response_envelope = yield from self.future()
        return response_envelope.result
