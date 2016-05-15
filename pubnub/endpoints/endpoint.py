from abc import ABCMeta, abstractmethod

from pubnub.errors import PNERR_SUBSCRIBE_KEY_MISSING, PNERR_PUBLISH_KEY_MISSING
from pubnub.exceptions import PubNubException
from ..structures import RequestOptions


class Endpoint:
    __metaclass__ = ABCMeta

    def __init__(self, pubnub):
        self.pubnub = pubnub

    @abstractmethod
    def build_path(self):
        pass

    @abstractmethod
    def build_params(self):
        pass

    @abstractmethod
    def http_method(self):
        pass

    @abstractmethod
    def validate_params(self):
        pass

    @abstractmethod
    def create_response(self, endpoint):
        pass

    def options(self):
        return RequestOptions(self.build_path(), self.build_params(), self.http_method())

    def sync(self):
        self.validate_params()

        server_response = self.pubnub.request_sync(self.options())

        response = self.create_response(server_response)

        return response

    def async(self, success, error):
        try:
            self.validate_params()
            options = self.options()
        except PubNubException as e:
            error(e)
            return

        def success_wrapper(server_response):
            success(self.create_response(server_response))

        def error_wrapper(msg):
            error(PubNubException(
                pn_error=msg
            ))

        return self.pubnub.request_async(options, success_wrapper, error_wrapper)

    def deferred(self):
        def handler():
            self.validate_params()
            return self.options()

        return self.pubnub.request_deferred(handler).addCallback(self.create_response)

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

    @classmethod
    def join_query(cls, params):
        query_list = []

        for k, v in params.items():
            query_list.append(k + "=" + v)

        return "&".join(query_list)
