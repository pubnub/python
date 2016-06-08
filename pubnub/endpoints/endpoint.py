import threading
from abc import ABCMeta, abstractmethod

from pubnub.enums import PNStatusCategory
from pubnub.errors import PNERR_SUBSCRIBE_KEY_MISSING, PNERR_PUBLISH_KEY_MISSING
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pn_error_data import PNErrorData
from ..structures import RequestOptions, ResponseInfo


class Endpoint(object):
    SERVER_RESPONSE_SUCCESS = 200
    SERVER_RESPONSE_FORBIDDEN = 403
    SERVER_RESPONSE_BAD_REQUEST = 400

    __metaclass__ = ABCMeta

    def __init__(self, pubnub):
        self.pubnub = pubnub
        # TODO: this is a platform-dependent operation
        self._cancellation_event = threading.Event()

    def cancellation_event(self, event):
        assert isinstance(event, threading.Event())
        self._cancellation_event = event

    @abstractmethod
    def build_path(self):
        pass

    @abstractmethod
    def build_params(self):
        pass

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
        pass

    @abstractmethod
    def name(self):
        pass

    def affected_channels(self):
        return None

    def affected_channels_groups(self):
        return None

    def options(self):
        return RequestOptions(self.build_path(), self.build_params(),
                              self.http_method(), self.build_data())

    def sync(self):
        self.validate_params()

        raw_response = self.pubnub.request_sync(self.options())
        return self.create_response(raw_response.json())

    def async(self, callback):
        try:
            self.validate_params()
            options = self.options()
        except PubNubException as e:
            callback(None, self.create_status_response(PNStatusCategory.PNBadRequestCategory, None, None, e))
            return

        def callback_wrapper(status_category, response, response_info, exception):
            callback(
                self.create_response(response),
                self.create_status_response(status_category, response, response_info, exception)
            )

        return self.pubnub.request_async(self.name(), options, callback_wrapper, self._cancellation_event)

    def future(self):
        def handler():
            self.validate_params()
            return self.options()

        return self.pubnub \
            .request_future(handler,
                            create_response=self.create_response,
                            create_status_response=self.create_status_response
                            )

    def deferred(self):
        def handler():
            self.validate_params()
            return self.options()

        # TODO: move .addCallback(self.create_response) logic to request_deferred()
        return self.pubnub \
            .request_deferred(handler) \
            .addCallback(self.create_response)

    def default_params(self):
        return {
            'pnsdk': self.pubnub.sdk_name,
            'uuid': self.pubnub.uuid
        }

    def validate_subscribe_key(self):
        if self.pubnub.config.subscribe_key is None or len(self.pubnub.config.subscribe_key) == 0:
            raise PubNubException(pn_error=PNERR_SUBSCRIBE_KEY_MISSING)

    def validate_publish_key(self):
        if self.pubnub.config.publish_key is None or len(self.pubnub.config.publish_key) == 0:
            raise PubNubException(pn_error=PNERR_PUBLISH_KEY_MISSING)

    def create_status_response(self, category, response, response_info, exception):
        """
        Used only by async requests

        :param category: of response
        :param response_info: unified response info
        :param response: already decoded json data
        :param exception: if any
        :return:
        """

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

        pn_status.operation = self.operation_type()
        pn_status.category = category
        pn_status.affected_channels = self.affected_channels()
        pn_status.affected_channels_groups = self.affected_channels_groups()

        return pn_status

    # TODO: move to utils?
    @classmethod
    def join_query(cls, params):
        query_list = []

        for k, v in params.items():
            query_list.append(k + "=" + v)

        return "&".join(query_list)
