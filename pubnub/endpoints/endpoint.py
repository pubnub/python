import string
from abc import ABCMeta, abstractmethod

# from pubnub import pubnub.PubNub
from pip._vendor import requests


class Endpoint:
    __metaclass__ = ABCMeta

    def __init__(self, pubnub):
        # assert isinstance(pubnub, pubnub.PubNub)
        self.pubnub = pubnub

    @abstractmethod
    def do_work(self):
        pass

    @abstractmethod
    def build_params(self):
        pass

    @abstractmethod
    def create_response(self, endpoint):
        pass

    def sync(self):
        server_response = self.do_work()

        # TODO: verify http success
        if server_response.status_code != requests.codes.ok:
            response_body_text = server_response.text
            print(response_body_text)
            # TODO: try to get text

        response = self.create_response(server_response)
        return response

    def default_params(self):
        return {
            'pnsdk': 'Python/' + self.pubnub.version,
            'uuid': self.pubnub.uuid
        }

    @classmethod
    def join_query(cls, params):
        query_list = []

        for k, v in params.items():
            query_list.append(k + "=" + v)

        return "&".join(query_list)
