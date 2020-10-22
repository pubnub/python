from pubnub.endpoints.endpoint import Endpoint


class FileOperationEndpoint(Endpoint):
    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = None

    def channel(self, channel):
        self._channel = channel
        return self

    def request_timeout(self):
        return self.pubnub.config.non_subscribe_request_timeout

    def connect_timeout(self):
        return self.pubnub.config.connect_timeout
