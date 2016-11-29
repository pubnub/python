from abc import ABCMeta, abstractmethod


class PNCallback(object):
    @abstractmethod
    def on_response(self, x, status):
        pass


class SubscribeCallback(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def status(self, pubnub, status):
        pass

    @abstractmethod
    def message(self, pubnub, message):
        pass

    @abstractmethod
    def presence(self, pubnub, presence):
        pass


class ReconnectionCallback(object):
    @abstractmethod
    def on_reconnect(self):
        pass
