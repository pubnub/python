from abc import ABCMeta, abstractmethod

from .endpoints.presence.herenow import HereNow


class PubNubAsync:
    """PubNub Python API for Python >= 3.5 with async/await syntax for asynchronous calls"""

    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def request_async(self, path, query):
        pass

    def here_now(self):
        return HereNow(self)

    @property
    def version(self):
        return "4.0.0"

    @property
    def uuid(self):
        return self.config.uuid
