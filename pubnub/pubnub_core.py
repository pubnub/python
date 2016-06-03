import logging
from abc import ABCMeta, abstractmethod

import requests

from .managers import PublishSequenceManager
from .endpoints.pubsub.publish import Publish
from .endpoints.presence.herenow import HereNow


logger = logging.getLogger("pubnub")


class PubNubCore:
    """A base class for PubNub Python API implementations"""
    SDK_VERSION = "4.0.0"
    SDK_NAME = "PubNub-Python"

    TIMESTAMP_DIVIDER = 1000
    MAX_SEQUENCE = 65535

    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config
        self.session = requests.Session()

        self.config.validate()
        self.headers = {
            'User-Agent': self.sdk_name
        }

        self.publish_sequence_manager = PublishSequenceManager(PubNubCore.MAX_SEQUENCE)

    @abstractmethod
    def request_deferred(self, options_func):
        pass

    def here_now(self):
        return HereNow(self)

    def publish(self):
        return Publish(self, self.publish_sequence_manager)

    @property
    def sdk_name(self):
        return "%s%s/%s" % (PubNubCore.SDK_NAME, self.sdk_platform(), PubNubCore.SDK_VERSION)

    @abstractmethod
    def sdk_platform(self): pass

    @property
    def uuid(self):
        return self.config.uuid
