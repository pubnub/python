from abc import ABCMeta, abstractmethod

from pubnub.exceptions import PubNubException


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
    def create_response(self, endpoint):
        pass

    def sync(self):
        # TODO: validate_params()
        server_response = self.pubnub.request_sync(self.build_path(), self.build_params())

        response = self.create_response(server_response)
        return response

    def async(self, success, error):
        def success_wrapper(server_response):
            success(self.create_response(server_response))

        def error_wrapper(msg):
            error(PubNubException(
                pn_error=msg
            ))

        return self.pubnub.request_async(self.build_path(), self.build_params(),
                                         success_wrapper, error_wrapper)

    def deferred(self):
        return self.pubnub.request_deferred(self.build_path(), self.build_params())\
            .addCallback(self.create_response)

    def default_params(self):
        return {
            'pnsdk': self.pubnub.sdk_name,
            'uuid': self.pubnub.uuid
        }

    @classmethod
    def join_query(cls, params):
        query_list = []

        for k, v in params.items():
            query_list.append(k + "=" + v)

        return "&".join(query_list)
