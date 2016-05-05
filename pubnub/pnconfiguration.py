
class PNConfiguration(object):
    def __init__(self):
        self.presence_timeout = 300
        # TODO: generate a random uuid
        self.uuid = ""
        self.origin = "pubsub.pubnub.com"
        self.ssl = False
        self.non_subscribe_request_timeout = 10
        self.subscribe_timeout = 310
        self.connect_timeout = 5
        self.subscribe_key = "demo"
        self.publish_key = "demo"

    def scheme(self):
        if self.ssl:
            return "https://"
        else:
            return "http://"

    def scheme_and_host(self):
        return self.scheme() + self.origin

        # TODO: set log level
        # TODO: set log level
