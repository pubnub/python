from pubnub.endpoints.file_operations.send_file import SendFileNative
from pubnub.endpoints.file_operations.publish_file_message import PublishFileMessage
from pubnub.endpoints.file_operations.fetch_upload_details import FetchFileUploadS3Data


class AsyncioSendFile(SendFileNative):
    async def future(self):
        self._file_upload_envelope = await FetchFileUploadS3Data(self._pubnub) \
            .channel(self._channel) \
            .file_name(self._file_name).future()

        response_envelope = await super(SendFileNative, self).future()

        publish_file_response = await PublishFileMessage(self._pubnub) \
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
            .cipher_key(self._cipher_key).future()

        response_envelope.result.timestamp = publish_file_response.result.timestamp
        return response_envelope

    async def result(self):
        response_envelope = await self.future()
        return response_envelope.result
