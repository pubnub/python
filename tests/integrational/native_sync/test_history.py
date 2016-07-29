import unittest
import logging
import time
import pubnub

from pubnub.models.consumer.history import PNHistoryResult
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf_copy, use_cassette_and_stub_time_sleep, pnconf_enc_copy

pubnub.set_stream_logger('pubnub', logging.DEBUG)

COUNT = 5


class TestPubNubState(unittest.TestCase):
    @use_cassette_and_stub_time_sleep('tests/integrational/fixtures/native_sync/history/basic.yaml',
                                      filter_query_parameters=['uuid'])
    def test_basic(self):
        ch = "history-native-sync-ch"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "history-native-sync-uuid"

        for i in range(COUNT):
            envelope = pubnub.publish().channel(ch).message("hey-%s" % i).sync()
            assert isinstance(envelope.result, PNPublishResult)
            assert envelope.result.timetoken > 0

        time.sleep(5)

        envelope = pubnub.history().channel(ch).count(COUNT).sync()

        assert isinstance(envelope.result, PNHistoryResult)
        assert envelope.result.start_timetoken > 0
        assert envelope.result.end_timetoken > 0
        assert len(envelope.result.messages) == 5

        assert envelope.result.messages[0].entry == 'hey-0'
        assert envelope.result.messages[1].entry == 'hey-1'
        assert envelope.result.messages[2].entry == 'hey-2'
        assert envelope.result.messages[3].entry == 'hey-3'
        assert envelope.result.messages[4].entry == 'hey-4'

    @use_cassette_and_stub_time_sleep('tests/integrational/fixtures/native_sync/history/encoded.yaml',
                                      filter_query_parameters=['uuid'])
    def test_encrypted(self):
        ch = "history-native-sync-ch"
        pubnub = PubNub(pnconf_enc_copy())
        pubnub.config.uuid = "history-native-sync-uuid"

        for i in range(COUNT):
            envelope = pubnub.publish().channel(ch).message("hey-%s" % i).sync()
            assert isinstance(envelope.result, PNPublishResult)
            assert envelope.result.timetoken > 0

        time.sleep(5)

        envelope = pubnub.history().channel(ch).count(COUNT).sync()

        assert isinstance(envelope.result, PNHistoryResult)
        assert envelope.result.start_timetoken > 0
        assert envelope.result.end_timetoken > 0
        assert len(envelope.result.messages) == 5

        assert envelope.result.messages[0].entry == 'hey-0'
        assert envelope.result.messages[1].entry == 'hey-1'
        assert envelope.result.messages[2].entry == 'hey-2'
        assert envelope.result.messages[3].entry == 'hey-3'
        assert envelope.result.messages[4].entry == 'hey-4'
