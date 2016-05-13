import json
import urllib

from pubnub.endpoints.endpoint import Endpoint
from pubnub.models.consumer.pubsub import PNPublishResult


class Publish(Endpoint):
    # /publish/<pub_key>/<sub_key>/<signature>/<channel>/<callback>/<message>[?argument(s)]
    PUBLISH_PATH = "/publish/%s/%s/0/%s/%s/%s"

    def __init__(self, pubnub):
        Endpoint.__init__(self, pubnub)
        self._channel = None
        self._message = None
        self._should_store = None
        self._use_post = False
        self._meta = {}

    def channel(self, channel):
        self._channel = channel
        return self

    def message(self, message):
        self._message = message
        return self

    def use_post(self, use_post):
        self._use_post = use_post
        return self

    def should_store(self, should_store):
        self._should_store = should_store
        return self

    def meta(self, meta):
        self._meta = meta
        return self

    def encode(self, data):
        if isinstance(data, str):
            return urllib.quote("\"%s\"" % data)
        else:
            return urllib.quote(json.dumps(data))

    def build_params(self):
        params = self.default_params()

        return params

    def build_path(self):
        message = self.encode(self._message)

        return Publish.PUBLISH_PATH % (self.pubnub.config.publish_key, self.pubnub.config.subscribe_key,
                                       self._channel, 0, message)

    def create_response(self, envelope):
        """
        :param envelope: an already serialized json response
        :return:
        """

        timetoken = int(envelope[2])

        res = PNPublishResult(timetoken)

        return res
