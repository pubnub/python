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

    def signal(self, pubnub, signal):
        pass

    def channel(self, pubnub, channel):
        pass

    def uuid(self, pubnub, uuid):
        pass

    def membership(self, pubnub, membership):
        pass

    def message_action(self, pubnub, message_action):
        pass

    def file(self, pubnub, file_message):
        pass


class ReconnectionCallback(object):
    @abstractmethod
    def on_reconnect(self):
        pass
