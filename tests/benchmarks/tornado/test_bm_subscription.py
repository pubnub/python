import logging

import tornado.gen
import tornado.locks
import tornado.ioloop

import pubnub as pn

from pubnub.callbacks import SubscribeCallback
from pubnub.pubnub_tornado import PubNubTornado
from tests.helper import pnconf

io_loop = tornado.ioloop.IOLoop.instance()
connected = tornado.locks.Event()

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "ch-bench"
count = 10


class SubscriptionBenchmarkListener(SubscribeCallback):
    def __init__(self):
        self.i = 0
        self.event = None

    def status(self, pubnub, status):
        connected.set()

    def presence(self, pubnub, presence):
        pass

    def message(self, pubnub, response):
        print("message#%d" % self.i)
        assert response.message == "hey-%d" % self.i
        self.i += 1
        self.event.set()

    def set_event(self, event):
        self.event = event

pubnub = PubNubTornado(pnconf, custom_ioloop=io_loop)
callback = SubscriptionBenchmarkListener()
pubnub.add_listener(callback)
pubnub.subscribe().channels(ch).execute()
connected.wait()


@tornado.gen.coroutine
def publish(i):
    yield pubnub.publish().channel(ch).message("hey-%d" % i).future()


@tornado.gen.coroutine
def cycle():
    event = tornado.locks.Event()
    io_loop.add_callback(publish, callback.i)
    callback.set_event(event)
    yield event.wait()


def runner():
    io_loop.run_sync(cycle)


def test_subscription_benchmark(benchmark):
    benchmark(runner)
    pubnub.stop()
    io_loop.stop()
