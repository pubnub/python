from tornado.locks import Event
from tornado import gen

from pubnub import utils
from pubnub.callbacks import SubscribeCallback


class ConnectionEvent(SubscribeCallback):
    def __init__(self, event, expected_status_checker):
        self.event = event
        self.expected_status_checker = expected_status_checker

    def status(self, pubnub, status):
        if self.expected_status_checker(status):
            self.event.set()

    def presence(self, pubnub, presence):
        pass

    def message(self, pubnub, message):
        pass


@gen.coroutine
def connect_to_channel(pubnub, channel):
    event = Event()
    callback = ConnectionEvent(event, utils.is_subscribed_event)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels(channel).execute()
    yield event.wait()


@gen.coroutine
def disconnect_from_channel(pubnub, channel):
    event = Event()
    callback = ConnectionEvent(event, utils.is_unsubscribed_event)
    pubnub.add_listener(callback)
    pubnub.unsubscribe().channels(channel).execute()
    yield event.wait()
