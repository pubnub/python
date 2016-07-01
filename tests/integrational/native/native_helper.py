import asyncio

from asyncio import Event, Queue
from pubnub.callbacks import SubscribeCallback
from tests import helper


class SubscribeListener(SubscribeCallback):
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
        self.message_queue.put(message)

    def presence(self, pubnub, presence):
        self.presence_queue.put(presence)

    @asyncio.coroutine
    def wait_for_connect(self):
        if not self.connected_event.is_set():
            yield from self.connected_event.wait()
        else:
            raise Exception("instance is already connected")

    @asyncio.coroutine
    def wait_for_disconnect(self):
        if not self.disconnected_event.is_set():
            yield from self.disconnected_event.wait()
        else:
            raise Exception("instance is already disconnected")

    @asyncio.coroutine
    def wait_for_message_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            try:
                env = yield from self.message_queue.get()
                if env.actual_channel in channel_names:
                    raise gen.Return(env)
                else:
                    continue
            finally:
                self.message_queue.task_done()

    @asyncio.coroutine
    def wait_for_presence_on(self, *channel_names):
        channel_names = list(channel_names)
        while True:
            try:
                env = yield from self.presence_queue.get()
                if env.actual_channel[:-7] in channel_names:
                    raise gen.Return(env)
                else:
                    continue
            finally:
                self.presence_queue.task_done()
