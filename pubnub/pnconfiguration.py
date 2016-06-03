from . import utils


class PNConfiguration(object):
    def __init__(self):
        # TODO: add validation
        self.presence_timeout = 300
        self.uuid = None
        self.origin = "pubsub.pubnub.com"
        self.ssl = False
        self.non_subscribe_request_timeout = 10
        self.subscribe_timeout = 310
        self.connect_timeout = 5
        self.subscribe_key = None
        self.publish_key = None
        self.cipher_key = None
        self.auth_key = None
        self.filter_expression = None
        self.enable_subscribe = True

    def validate(self):
        assert self.uuid is None or isinstance(self.uuid, str)

        if self.uuid is None:
            self.uuid = utils.uuid()

    def scheme(self):
        if self.ssl:
            return "https"
        else:
            return "http"

    def scheme_extended(self):
        return self.scheme() + "://"

    def scheme_and_host(self):
        return self.scheme_extended() + self.origin

        # TODO: set log level
        # TODO: set log level
