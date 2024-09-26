import logging
import asyncio

import pytest
from pubnub.enums import PNOperationType, PNStatusCategory

from pubnub.callbacks import SubscribeCallback

import pubnub as pn

from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_pam_copy
# from tests.integrational.vcr_helper import pn_vcr

pn.set_stream_logger('pubnub', logging.DEBUG)


class AccessDeniedListener(SubscribeCallback):
    def __init__(self):
        self.access_denied_event = asyncio.Event()

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        pass

    def status(self, pubnub, status):
        disconnected = PNStatusCategory.PNDisconnectedCategory
        denied = status.operation == PNOperationType.PNUnsubscribeOperation and \
            status.category == PNStatusCategory.PNAccessDeniedCategory

        if disconnected or denied:
            self.access_denied_event.set()


class ReconnectedListener(SubscribeCallback):
    def __init__(self):
        self.reconnected_event = asyncio.Event()

    def message(self, pubnub, message):
        pass

    def presence(self, pubnub, presence):
        pass

    def status(self, pubnub, status):
        disconnected = PNStatusCategory.PNDisconnectedCategory
        denied = status.operation == PNOperationType.PNUnsubscribeOperation and \
            status.category == PNStatusCategory.PNAccessDeniedCategory

        if disconnected or denied:
            self.access_denied_event.set()


# @pn_vcr.use_cassette(
#     'tests/integrational/fixtures/asyncio/subscription/access_denied_unsubscribe_operation.yaml',
#     filter_query_parameters=['pnsdk', 'l_cg', 'l_pres'],
#     match_on=['method', 'scheme', 'host', 'port', 'string_list_in_path', 'string_list_in_query'],
# )
@pytest.mark.asyncio
async def test_access_denied_unsubscribe_operation():
    channel = "not-permitted-channel"
    pnconf = pnconf_pam_copy()
    pnconf.secret_key = None
    pnconf.enable_subscribe = True
    pnconf.reconnect_policy = pn.enums.PNReconnectionPolicy.NONE

    pubnub = PubNubAsyncio(pnconf)

    callback = AccessDeniedListener()
    pubnub.add_listener(callback)

    pubnub.subscribe().channels(channel).execute()
    await callback.access_denied_event.wait()

    await pubnub.stop()
