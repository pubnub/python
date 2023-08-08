import asyncio
import logging
import pytest
import sys

from unittest.mock import patch
from tests.helper import pnconf_env_copy

from pubnub.pubnub_asyncio import PubNubAsyncio, EventEngineSubscriptionManager, SubscribeCallback
from pubnub.event_engine.models import states
from pubnub.models.consumer.common import PNStatus
from pubnub.enums import PNStatusCategory

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


class TestCallback(SubscribeCallback):
    def status(self, pubnub, status: PNStatus):
        assert status.error is False
        assert status.category is PNStatusCategory.PNConnectedCategory
        self.status_called()

    def message(self, pubnub, message):
        assert message.channel == 'foo'
        assert message.message == 'test'
        self.message_called()

    def status_called(self):
        pass

    def message_called(self):
        pass


@pytest.mark.asyncio
@pytest.mark.skip
@patch.object(TestCallback, 'status_called')
@patch.object(TestCallback, 'message_called')
async def test_subscribe(mocked_status, mocked_message):
    loop = asyncio.get_event_loop()
    config = pnconf_env_copy()
    config.enable_subscribe = True
    callback = TestCallback()
    pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager, custom_event_loop=loop)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels('foo').execute()
    await delayed_publish('foo', 'test', 1)
    await asyncio.sleep(5)
    assert pubnub._subscription_manager.event_engine.get_state_name() == states.ReceivingState.__name__
    # mocked_status.assert_called()
    # mocked_message.assert_called()
    pubnub.unsubscribe_all()
    await asyncio.sleep(1)
    pubnub._subscription_manager.stop()

    try:
        await asyncio.gather(*asyncio.tasks.all_tasks())
    except asyncio.CancelledError:
        pass
    await asyncio.sleep(0)
    await pubnub.close_session()


async def delayed_publish(channel, message, delay):
    pn = PubNubAsyncio(pnconf_env_copy())
    await asyncio.sleep(delay)
    await pn.publish().channel(channel).message(message).future()


@pytest.mark.asyncio
@pytest.mark.skip
@patch.object(TestCallback, 'status_called')
async def test_handshaking(mocked_status):
    config = pnconf_env_copy()
    config.enable_subscribe = True
    callback = TestCallback()
    pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager)
    pubnub.add_listener(callback)
    pubnub.subscribe().channels('foo').execute()
    await asyncio.sleep(1)
    assert pubnub._subscription_manager.event_engine.get_state_name() == states.ReceivingState.__name__
    # mocked_status.assert_called()
    pubnub._subscription_manager.stop()
    await asyncio.sleep(2)

    try:
        await asyncio.gather(*asyncio.tasks.all_tasks())
    except asyncio.CancelledError:
        pass
    await pubnub.close_session()
