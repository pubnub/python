import unittest

from pubnub import utils
from pubnub.models.consumer.objects_v2.memberships import PNChannelMembership
from pubnub.pubnub import PubNub, SubscribeListener
from tests.helper import pnconf_copy


def _pubnub():
    config = pnconf_copy()
    # use subscribe key that associated with app that has Objects turned on and comment skip annotation
    config.subscribe_key = "SUBSCRIBE_KEY"
    config.log_verbosity = True
    config.enable_subscribe = True
    return PubNub(config)


class TestObjectsV2Callbacks:
    @unittest.skip("Needs real subscribe key and real traffic. Hard to implement using vcr")
    def test_callbacks(self):
        pn = _pubnub()
        subscribe_listener = SubscribeListener()
        pn.add_listener(subscribe_listener)

        test_channel = "test_ch1_%s" % utils.uuid()

        pn.subscribe() \
            .channels([test_channel]) \
            .execute()

        subscribe_listener.wait_for_connect()

        pn.set_channel_metadata() \
            .channel(test_channel) \
            .set_name("The channel %s" + utils.uuid()) \
            .sync()

        pn.set_memberships() \
            .channel_memberships([PNChannelMembership.channel(test_channel)]) \
            .sync()

        pn.set_uuid_metadata() \
            .set_name("Some Name %s" + utils.uuid()) \
            .email("test@example.com") \
            .sync()

        membership_result = subscribe_listener.membership_queue.get(block=True, timeout=10)
        channel_result = subscribe_listener.channel_queue.get(block=True, timeout=10)
        uuid_result = subscribe_listener.uuid_queue.get(block=True, timeout=10)

        assert membership_result is not None
        assert channel_result is not None
        assert uuid_result is not None
