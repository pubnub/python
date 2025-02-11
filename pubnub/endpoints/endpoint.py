from abc import ABCMeta, abstractmethod

import logging
import zlib

from pubnub import utils
from pubnub.enums import PNStatusCategory, HttpMethod
from pubnub.errors import (
    PNERR_SUBSCRIBE_KEY_MISSING, PNERR_PUBLISH_KEY_MISSING, PNERR_CHANNEL_OR_GROUP_MISSING,
    PNERR_SECRET_KEY_MISSING, PNERR_CHANNEL_MISSING, PNERR_FILE_OBJECT_MISSING,
    PNERR_FILE_ID_MISSING, PNERR_FILE_NAME_MISSING
)
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pn_error_data import PNErrorData
from pubnub.structures import RequestOptions, ResponseInfo

logger = logging.getLogger("pubnub")


class Endpoint(object):
    SERVER_RESPONSE_SUCCESS = 200
    SERVER_RESPONSE_FORBIDDEN = 403
    SERVER_RESPONSE_BAD_REQUEST = 400

    __metaclass__ = ABCMeta
    _path = None
    _custom_headers: dict = None

    def __init__(self, pubnub):
        self.pubnub = pubnub
        self._cancellation_event = None
        self._sort_params = False
        self._use_compression = self.pubnub.config.should_compress

    def cancellation_event(self, event):
        self._cancellation_event = event
        return self

    @abstractmethod
    def build_path(self):
        pass

    @abstractmethod
    def custom_params(self):
        raise NotImplementedError

    def build_data(self):
        return None

    @abstractmethod
    def http_method(self):
        pass

    @abstractmethod
    def validate_params(self):
        pass

    @abstractmethod
    def create_response(self, endpoint):
        pass

    @abstractmethod
    def operation_type(self):
        raise NotImplementedError

    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def request_timeout(self):
        pass

    @abstractmethod
    def connect_timeout(self):
        pass

    def is_auth_required(self):
        raise NotImplementedError

    def affected_channels(self):
        return None

    def affected_channels_groups(self):
        return None

    def allow_redirects(self):
        return True

    def use_base_path(self):
        return True

    def is_compressable(self):
        return False

    def request_headers(self):
        headers = {}
        if self.__compress_request():
            headers["Content-Encoding"] = "gzip"
        if self.http_method() in [HttpMethod.POST, HttpMethod.PATCH]:
            headers["Content-type"] = "application/json"

        if self._custom_headers:
            headers.update(self._custom_headers)

        return headers

    def build_file_upload_request(self):
        return

    def non_json_response(self):
        return False

    def encoded_params(self):
        return {}

    def get_path(self):
        if not self._path:
            self._path = self.build_path()
        return self._path

    def options(self):
        data = self.build_data()
        if data and self.__compress_request():
            data = zlib.compress(data.encode('utf-8'), level=2)
        return RequestOptions(
            path=self.get_path(),
            params_callback=self.build_params_callback(),
            method=self.http_method(),
            request_timeout=self.request_timeout(),
            connect_timeout=self.connect_timeout(),
            create_response=self.create_response,
            create_status=self.create_status,
            create_exception=self.create_exception,
            operation_type=self.operation_type(),
            data=data,
            files=self.build_file_upload_request(),
            sort_arguments=self._sort_params,
            allow_redirects=self.allow_redirects(),
            use_base_path=self.use_base_path(),
            request_headers=self.request_headers(),
            non_json_response=self.non_json_response()
        )

    def sync(self):
        self.validate_params()
        envelope = self.pubnub.request_sync(self.options())

        if envelope.status.is_error():
            raise envelope.status.error_data.exception

        return envelope

    def prepare_options(self):
        return self.pubnub.prepare_options(self.options())

    def pn_async(self, callback):
        try:
            self.validate_params()
            options = self.options()
        except PubNubException as e:
            callback(None, self.create_status(PNStatusCategory.PNBadRequestCategory, None, None, e))
            return

        def callback_wrapper(envelope):
            callback(envelope.result, envelope.status)

        return self.pubnub.request_async(endpoint_name=self.name(),
                                         endpoint_call_options=options,
                                         callback=callback_wrapper,
                                         # REVIEW: include self._cancellation_event into options?
                                         cancellation_event=self._cancellation_event)

    def result(self):
        def handler():
            self.validate_params()
            return self.options()

        return self.pubnub.request_result(options_func=handler,
                                          cancellation_event=self._cancellation_event)

    def future(self):
        def handler():
            self.validate_params()
            return self.options()

        return self.pubnub.request_future(options_func=handler,
                                          cancellation_event=self._cancellation_event)

    def deferred(self):
        def handler():
            self.validate_params()
            return self.options()

        return self.pubnub.request_deferred(options_func=handler,
                                            cancellation_event=self._cancellation_event)

    def build_params_callback(self):
        def callback(params_to_merge):
            custom_params = self.custom_params()
            custom_params.update(params_to_merge)

            custom_params['pnsdk'] = self.pubnub.sdk_name
            custom_params['uuid'] = self.pubnub.uuid

            for query_key, query_value in self.pubnub._telemetry_manager.operation_latencies().items():
                custom_params[query_key] = query_value

            if self.is_auth_required():
                if self.pubnub._get_token():
                    custom_params["auth"] = self.pubnub._get_token()
                elif self.pubnub.config.auth_key:
                    custom_params["auth"] = self.pubnub.config.auth_key

            if self.pubnub.config.secret_key:
                utils.sign_request(self, self.pubnub, custom_params, self.http_method(), self.build_data())

            custom_params.update(self.encoded_params())

            # reassign since pnsdk should be signed unencoded
            custom_params['pnsdk'] = utils.url_encode(self.pubnub.sdk_name)

            return custom_params

        return callback

    def validate_subscribe_key(self):
        if self.pubnub.config.subscribe_key is None or len(self.pubnub.config.subscribe_key) == 0:
            raise PubNubException(pn_error=PNERR_SUBSCRIBE_KEY_MISSING)

    def validate_secret_key(self):
        if self.pubnub.config.secret_key is None or len(self.pubnub.config.secret_key) == 0:
            raise PubNubException(pn_error=PNERR_SECRET_KEY_MISSING)

    def validate_channel(self):
        if self._channel is None or len(self._channel) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_MISSING)

    def validate_channels_and_groups(self):
        if len(self._channels) == 0 and len(self._groups) == 0:
            raise PubNubException(pn_error=PNERR_CHANNEL_OR_GROUP_MISSING)

    def validate_publish_key(self):
        if self.pubnub.config.publish_key is None or len(self.pubnub.config.publish_key) == 0:
            raise PubNubException(pn_error=PNERR_PUBLISH_KEY_MISSING)

    def validate_file_object(self):
        if not self._file_object:
            raise PubNubException(pn_error=PNERR_FILE_OBJECT_MISSING)

    def validate_file_name(self):
        if not self._file_name:
            raise PubNubException(pn_error=PNERR_FILE_NAME_MISSING)

    def validate_file_id(self):
        if not self._file_id:
            raise PubNubException(pn_error=PNERR_FILE_ID_MISSING)

    def create_status(self, category, response, response_info, exception):
        if response_info is not None:
            assert isinstance(response_info, ResponseInfo)

        pn_status = PNStatus()

        if response is None or exception is not None:
            pn_status.error = True

        if response is not None:
            pn_status.original_response = response

        if exception is not None:
            pn_status.error_data = PNErrorData(str(exception), exception)

        if response_info is not None:
            pn_status.status_code = response_info.status_code
            pn_status.tls_enabled = response_info.tls_enabled
            pn_status.origin = response_info.origin
            pn_status.uuid = response_info.uuid
            pn_status.auth_key = response_info.auth_key
            pn_status.client_request = response_info.client_request
            pn_status.client_response = response_info.client_response

        pn_status.operation = self.operation_type()
        pn_status.category = category
        pn_status.affected_channels = self.affected_channels()
        pn_status.affected_groups = self.affected_channels_groups()

        return pn_status

    """ Used by asyncio and tornado clients to build exceptions

    The only difference with create_status() method is that a status
    is wrapped with an exception and also contains this exception inside
    as 'status.error_data.exception'
    """

    def create_exception(self, category, response, response_info, exception):
        status = self.create_status(category, response, response_info, exception)

        exception.status = status

        return exception

    def __compress_request(self):
        return (self.is_compressable() and self._use_compression)
