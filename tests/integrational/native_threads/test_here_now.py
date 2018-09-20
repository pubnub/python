import unittest
import logging
import time
import pubnub
import threading

from pubnub.pubnub import PubNub, SubscribeListener, NonSubscribeListener
from tests import helper
from tests.helper import pnconf_sub_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(unittest.TestCase):
    def setUp(self):
        self.event = threading.Event()

    def callback(self, response, status):
        self.response = response
        self.status = status
        self.event.set()

    def test_single_channel(self):
        pubnub = PubNub(pnconf_sub_copy())
        ch = helper.gen_channel("herenow-asyncio-channel")
        uuid = helper.gen_channel("herenow-asyncio-uuid")
        pubnub.config.uuid = uuid

        subscribe_listener = SubscribeListener()
        here_now_listener = NonSubscribeListener()
        pubnub.add_listener(subscribe_listener)
        pubnub.subscribe().channels(ch).execute()

        subscribe_listener.wait_for_connect()

        time.sleep(2)

        pubnub.here_now() \
            .channels(ch) \
            .include_uuids(True) \
            .pn_async(here_now_listener.callback)

        if here_now_listener.pn_await() is False:
            self.fail("HereNow operation timeout")

        result = here_now_listener.result
        channels = result.channels

        assert len(channels) == 1
        assert channels[0].occupancy == 1
        assert channels[0].occupants[0].uuid == pubnub.uuid

        pubnub.unsubscribe().channels(ch).execute()
        subscribe_listener.wait_for_disconnect()

        pubnub.stop()

    def test_multiple_channels(self):
        pubnub = PubNub(pnconf_sub_copy())
        ch1 = helper.gen_channel("here-now-native-sync-ch1")
        ch2 = helper.gen_channel("here-now-native-sync-ch2")
        pubnub.config.uuid = "here-now-native-sync-uuid"

        subscribe_listener = SubscribeListener()
        here_now_listener = NonSubscribeListener()
        pubnub.add_listener(subscribe_listener)
        pubnub.subscribe().channels([ch1, ch2]).execute()

        subscribe_listener.wait_for_connect()

        time.sleep(5)

        pubnub.here_now() \
            .channels([ch1, ch2]) \
            .pn_async(here_now_listener.callback)

        if here_now_listener.pn_await() is False:
            self.fail("HereNow operation timeout")

        result = here_now_listener.result
        channels = result.channels

        assert len(channels) == 2
        assert channels[0].occupancy == 1
        assert channels[0].occupants[0].uuid == pubnub.uuid
        assert channels[1].occupancy == 1
        assert channels[1].occupants[0].uuid == pubnub.uuid

        pubnub.unsubscribe().channels([ch1, ch2]).execute()
        subscribe_listener.wait_for_disconnect()

        pubnub.stop()
