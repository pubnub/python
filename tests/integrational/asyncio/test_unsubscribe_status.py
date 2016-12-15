import logging
import asyncio
import pytest
from pubnub.enums import PNOperationType, PNStatusCategory

from pubnub.callbacks import SubscribeCallback

import pubnub as pn

from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_pam_copy

pn.set_stream_logger('pubnub', logging.DEBUG)


class AccessDeniedListener(SubscribeCallback):
    def __init__(self):
        self.access_denied_event = asyncio.Event()

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        pass

    def status(self, pubnub, status):
        if status.operation == PNOperationType.PNUnsubscribeOperation:
            if status.category == PNStatusCategory.PNAccessDeniedCategory:
                self.access_denied_event.set()


class ReconnectedListener(SubscribeCallback):
    def __init__(self):
        self.reconnected_event = asyncio.Event()

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        pass

    def status(self, pubnub, status):
        if status.operation == PNOperationType.PNUnsubscribeOperation:
            if status.category == PNStatusCategory.PNReconnectedCategory:
                self.reconnected_event.set()


@pytest.mark.asyncio
def test_access_denied_unsubscribe_operation(event_loop):
    channel = "not-permitted-channel"
    pnconf = pnconf_pam_copy()
    pnconf.secret_key = None
    pnconf.enable_subscribe = True

    pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)

    callback = AccessDeniedListener()
    pubnub.add_listener(callback)

    pubnub.subscribe().channels(channel).execute()
    yield from callback.access_denied_event.wait()

    pubnub.stop()

#
# @pytest.mark.asyncio
# async def test_reconnected_unsubscribe_operation(event_loop):
#     channel = "not-permitted-channel"
#     pnconf = pnconf_pam_copy()
#     pnconf.enable_subscribe = True
#
#     pubnub = PubNubAsyncio(pnconf, custom_event_loop=event_loop)
#
#     callback = ReconnectedListener()
#     pubnub.add_listener(callback)
#
#     pubnub.subscribe().channels(channel).execute()
#     await callback.reconnected_event.wait()
#
#     pubnub.stop()
