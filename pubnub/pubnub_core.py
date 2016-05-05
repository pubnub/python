from abc import ABCMeta, abstractmethod

from .endpoints.presence.herenow import HereNow


class PubNubCore:
    """PubNub Python API"""

    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def request(self, path, query):
        pass

    def here_now(self):
        return HereNow(self)

    @property
    def version(self):
        return "4.0.0"

    @property
    def uuid(self):
        return self.config.uuid
