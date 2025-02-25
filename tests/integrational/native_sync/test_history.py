import binascii
import logging
import time
import unittest
import pubnub
import pytest

from unittest.mock import patch
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.history import PNHistoryResult
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf_copy, pnconf_enc_copy, pnconf_enc_env_copy, pnconf_env_copy, pnconf_pam_copy, \
    pnconf_pam_stub_copy
from tests.integrational.vcr_helper import use_cassette_and_stub_time_sleep_native

pubnub.set_stream_logger('pubnub', logging.DEBUG)

COUNT = 5


class TestPubNubHistory(unittest.TestCase):
    @use_cassette_and_stub_time_sleep_native('tests/integrational/fixtures/native_sync/history/basic.yaml',
                                             filter_query_parameters=['uuid', 'pnsdk', 'l_pub'])
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

    @patch("pubnub.crypto.PubNubCryptodome.get_initialization_vector", return_value="knightsofni12345")
    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/history/encoded.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub']
    )
    def test_encrypted(self, crypto_mock):
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

    def test_not_permitted(self):
        ch = "history-native-sync-ch"
        pubnub = PubNub(pnconf_pam_stub_copy(non_subscribe_request_timeout=1))
        pubnub.config.uuid = "history-native-sync-uuid"

        with pytest.raises(PubNubException):
            pubnub.history().channel(ch).count(5).sync()

    def test_super_call_with_channel_only(self):
        ch = "history-native-sync-ch"
        pubnub = PubNub(pnconf_pam_copy())
        pubnub.config.uuid = "history-native-sync-uuid"

        envelope = pubnub.history().channel(ch).sync()
        assert isinstance(envelope.result, PNHistoryResult)

        assert not envelope.status.is_error()

    def test_super_call_with_all_params(self):
        ch = "history-native-sync-ch"
        pubnub = PubNub(pnconf_pam_copy())
        pubnub.config.uuid = "history-native-sync-uuid"

        envelope = pubnub.history().channel(ch).count(2).include_timetoken(True).reverse(True).start(1).end(2).sync()
        assert isinstance(envelope.result, PNHistoryResult)

        assert not envelope.status.is_error()


class TestHistoryCrypto(unittest.TestCase):
    @use_cassette_and_stub_time_sleep_native('tests/integrational/fixtures/native_sync/history/unencrypted.json',
                                             serializer='pn_json', filter_query_parameters=['uuid', 'pnsdk'])
    def test_unencrypted(self):
        ch = "test_unencrypted"
        pubnub = PubNub(pnconf_env_copy())
        pubnub.config.uuid = "history-native-sync-uuid"
        pubnub.delete_messages().channel(ch).sync()
        envelope = pubnub.publish().channel(ch).message("Lorem Ipsum").sync()
        assert isinstance(envelope.result, PNPublishResult)
        assert envelope.result.timetoken > 0

        time.sleep(2)

        pubnub_enc = PubNub(pnconf_enc_env_copy())
        pubnub_enc.config.uuid = "history-native-sync-uuid"
        envelope = pubnub_enc.history().channel(ch).sync()

        assert isinstance(envelope.result, PNHistoryResult)
        assert envelope.result.start_timetoken > 0
        assert envelope.result.end_timetoken > 0
        assert len(envelope.result.messages) == 1

        assert envelope.result.messages[0].entry == 'Lorem Ipsum'
        assert isinstance(envelope.result.messages[0].error, binascii.Error)
