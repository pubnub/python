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
            result = pubnub.publish().channel(ch).message("hey-%s" % i).sync()
            assert isinstance(result, PNPublishResult)
            assert result.timetoken > 0

        time.sleep(5)

        result = pubnub.history().channel(ch).count(COUNT).sync()

        assert isinstance(result, PNHistoryResult)
        assert result.start_timetoken > 0
        assert result.end_timetoken > 0
        assert len(result.messages) == 5

        assert result.messages[0].entry == 'hey-0'
        assert result.messages[1].entry == 'hey-1'
        assert result.messages[2].entry == 'hey-2'
        assert result.messages[3].entry == 'hey-3'
        assert result.messages[4].entry == 'hey-4'

    @use_cassette_and_stub_time_sleep('tests/integrational/fixtures/native_sync/history/encoded.yaml',
                                      filter_query_parameters=['uuid'])
    def test_encrypted(self):
        ch = "history-native-sync-ch"
        pubnub = PubNub(pnconf_enc_copy())
        pubnub.config.uuid = "history-native-sync-uuid"

        for i in range(COUNT):
            result = pubnub.publish().channel(ch).message("hey-%s" % i).sync()
            assert isinstance(result, PNPublishResult)
            assert result.timetoken > 0

        time.sleep(5)

        result = pubnub.history().channel(ch).count(COUNT).sync()

        assert isinstance(result, PNHistoryResult)
        assert result.start_timetoken > 0
        assert result.end_timetoken > 0
        assert len(result.messages) == 5

        assert result.messages[0].entry == 'hey-0'
        assert result.messages[1].entry == 'hey-1'
        assert result.messages[2].entry == 'hey-2'
        assert result.messages[3].entry == 'hey-3'
        assert result.messages[4].entry == 'hey-4'
