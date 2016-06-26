from tornado.locks import Event
from tornado import gen
from tornado.queues import Queue

from pubnub.callbacks import SubscribeCallback
from tests import helper


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


class ExtendedSubscribeCallback(SubscribeCallback):
    def __init__(self):
        self.connected = False
        self.connected_event = Event()
        self.disconnected_event = Event()
        self.presence_queue = Queue()
        self.message_queue = Queue()

    def status(self, pubnub, status):
        if helper.is_subscribed_event(status) and not self.connected_event.is_set():
            self.connected_event.set()
        elif helper.is_unsubscribed_event(status) and not self.disconnected_event.is_set():
            self.disconnected_event.set()

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        self.presence_queue.put(presence)

    @gen.coroutine
    def wait_for_connect(self):
        if not self.connected_event.is_set():
            yield self.connected_event.wait()
        else:
            raise Exception("instance is already connected")

    @gen.coroutine
    def wait_for_disconnect(self):
        if not self.disconnected_event.is_set():
            yield self.disconnected_event.wait()
        else:
            raise Exception("instance is already disconnected")

    @gen.coroutine
    def wait_for_presence_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            try:
                env = yield self.presence_queue.get()
                if env.actual_channel[:-7] in channel_names:
                    raise gen.Return(env)
                else:
                    continue
            finally:
                self.presence_queue.task_done()
        if not self.connected_event.is_set():
            yield self.connected_event.wait()


@gen.coroutine
def connect_to_channel(pubnub, channel):
    event = Event()
    callback = ConnectionEvent(event, helper.is_subscribed_event)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels(channel).execute()
    yield event.wait()


@gen.coroutine
def disconnect_from_channel(pubnub, channel):
    event = Event()
    callback = ConnectionEvent(event, helper.is_unsubscribed_event)
    pubnub.add_listener(callback)
    pubnub.unsubscribe().channels(channel).execute()
    yield event.wait()

