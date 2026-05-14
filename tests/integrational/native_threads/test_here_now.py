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
        config = pnconf_sub_copy()
        config.daemon = True
        pn = PubNub(config)
        ch = helper.gen_channel("herenow-asyncio-channel")
        uuid = helper.gen_channel("herenow-asyncio-uuid")
        pn.config.uuid = uuid

        subscribe_listener = SubscribeListener()
        here_now_listener = NonSubscribeListener()
        pn.add_listener(subscribe_listener)
        pn.subscribe().channels(ch).execute()

        try:
            subscribe_listener.wait_for_connect()
            time.sleep(2)

            pn.here_now() \
                .channels(ch) \
                .include_uuids(True) \
                .pn_async(here_now_listener.callback)

            if here_now_listener.pn_await() is False:
                self.fail("HereNow operation timeout")

            result = here_now_listener.result
            channels = result.channels

            assert len(channels) == 1
            assert channels[0].occupancy == 1
            assert channels[0].occupants[0].uuid == pn.uuid

            pn.unsubscribe().channels(ch).execute()
            subscribe_listener.wait_for_disconnect()
        finally:
            pn.stop()

    def test_multiple_channels(self):
        config = pnconf_sub_copy()
        config.daemon = True
        pn = PubNub(config)
        ch1 = helper.gen_channel("here-now-native-sync-ch1")
        ch2 = helper.gen_channel("here-now-native-sync-ch2")
        pn.config.uuid = "here-now-native-sync-uuid"

        subscribe_listener = SubscribeListener()
        here_now_listener = NonSubscribeListener()
        pn.add_listener(subscribe_listener)
        pn.subscribe().channels([ch1, ch2]).execute()

        try:
            subscribe_listener.wait_for_connect()
            time.sleep(5)

            pn.here_now() \
                .channels([ch1, ch2]) \
                .pn_async(here_now_listener.callback)

            if here_now_listener.pn_await() is False:
                self.fail("HereNow operation timeout")

            result = here_now_listener.result
            channels = result.channels

            assert len(channels) == 2
            assert channels[0].occupancy == 1
            assert channels[0].occupants[0].uuid == pn.uuid
            assert channels[1].occupancy == 1
            assert channels[1].occupants[0].uuid == pn.uuid

            pn.unsubscribe().channels([ch1, ch2]).execute()
            subscribe_listener.wait_for_disconnect()
        finally:
            pn.stop()
