import unittest
import logging
import pubnub
import time

from pubnub.pubnub import PubNub, SubscribeListener, NonSubscribeListener
from tests import helper
from tests.helper import pnconf_env_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubState(unittest.TestCase):
    def test_single_channel(self):
        ch = helper.gen_channel("wherenow-native-ch")
        uuid = helper.gen_channel("wherenow-native-uuid")
        config = pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True)
        config.uuid = uuid
        pn = PubNub(config)

        subscribe_listener = SubscribeListener()
        where_now_listener = NonSubscribeListener()
        pn.add_listener(subscribe_listener)
        pn.subscribe().channels(ch).execute()

        try:
            subscribe_listener.wait_for_connect()
            time.sleep(5)

            pn.where_now() \
                .uuid(uuid) \
                .pn_async(where_now_listener.callback)

            if where_now_listener.pn_await() is False:
                self.fail("WhereNow operation timeout")

            result = where_now_listener.result
            channels = result.channels

            assert len(channels) == 1
            assert channels[0] == ch

            pn.unsubscribe().channels(ch).execute()
            subscribe_listener.wait_for_disconnect()
        finally:
            pn.stop()

    def test_multiple_channels(self):
        ch1 = helper.gen_channel("state-native-sync-ch-1")
        ch2 = helper.gen_channel("state-native-sync-ch-2")
        uuid = helper.gen_channel("state-native-sync-uuid")
        config = pnconf_env_copy(enable_subscribe=True, daemon=True, enable_presence_heartbeat=True)
        config.uuid = uuid
        pn = PubNub(config)

        subscribe_listener = SubscribeListener()
        where_now_listener = NonSubscribeListener()
        pn.add_listener(subscribe_listener)
        pn.subscribe().channels([ch1, ch2]).execute()

        try:
            subscribe_listener.wait_for_connect()
            time.sleep(5)

            pn.where_now() \
                .uuid(uuid) \
                .pn_async(where_now_listener.callback)

            if where_now_listener.pn_await() is False:
                self.fail("WhereNow operation timeout")

            result = where_now_listener.result
            channels = result.channels

            assert len(channels) == 2
            assert ch1 in channels
            assert ch2 in channels

            pn.unsubscribe().channels([ch1, ch2]).execute()
            subscribe_listener.wait_for_disconnect()
        finally:
            pn.stop()
