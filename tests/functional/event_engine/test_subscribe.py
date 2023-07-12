import asyncio
import logging
import pytest
import sys

from unittest.mock import patch
from tests.helper import pnconf_env_copy

from pubnub.pubnub_asyncio import PubNubAsyncio, EventEngineSubscriptionManager, SubscribeCallback
from pubnub.event_engine.models import states

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


@pytest.mark.asyncio
async def test_subscribe_triggers_event():
    config = pnconf_env_copy()
    config.enable_subscribe = True

    pubnub = PubNubAsyncio(config, subscription_manager=EventEngineSubscriptionManager)

    with patch.object(SubscribeCallback, 'status') as mocked_status, \
            patch.object(SubscribeCallback, 'message') as mocked_message:
        callback = SubscribeCallback()
        pubnub.add_listener(callback)
        pubnub.subscribe().channels('foo').execute()
        await delayed_publish('foo', 'test', 2)
        await asyncio.sleep(5)
        assert pubnub._subscription_manager.event_engine.get_state_name() == states.ReceivingState.__name__
        mocked_status.assert_called()
        mocked_message.assert_called()
        pubnub.unsubscribe_all()
        await asyncio.sleep(2)
        pubnub._subscription_manager.stop()
        await asyncio.sleep(0.1)


async def delayed_publish(channel, message, delay):
    pn = PubNubAsyncio(pnconf_env_copy())
    await asyncio.sleep(delay)
    await pn.publish().channel(channel).message(message).future()
