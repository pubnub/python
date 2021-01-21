import aiohttp

from pubnub.endpoints.file_operations.send_file import SendFileNative
from pubnub.endpoints.file_operations.publish_file_message import PublishFileMessage
from pubnub.endpoints.file_operations.fetch_upload_details import FetchFileUploadS3Data


class AsyncioSendFile(SendFileNative):
    def build_file_upload_request(self):
        file = self.encrypt_payload()
        form_data = aiohttp.FormData()
        for form_field in self._file_upload_envelope.result.data["form_fields"]:
            form_data.add_field(form_field["key"], form_field["value"], content_type="multipart/form-data")
        form_data.add_field("file", file, filename=self._file_name, content_type="application/octet-stream")

        return form_data

    def options(self):
        request_options = super(SendFileNative, self).options()
        request_options.data = request_options.files
        return request_options

    async def future(self):
        self._file_upload_envelope = await FetchFileUploadS3Data(self._pubnub).\
            channel(self._channel).\
            file_name(self._file_name).future()

        response_envelope = await super(SendFileNative, self).future()

        publish_file_response = await PublishFileMessage(self._pubnub).\
            channel(self._channel).\
            meta(self._meta).\
            message(self._message).\
            file_id(response_envelope.result.file_id).\
            file_name(response_envelope.result.name).\
            should_store(self._should_store).\
            ttl(self._ttl).\
            cipher_key(self._cipher_key).future()

        response_envelope.result.timestamp = publish_file_response.result.timestamp
        return response_envelope

    async def result(self):
        response_envelope = await self.future()
        return response_envelope.result
