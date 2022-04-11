import time

from pubnub.models.consumer.history import PNFetchMessagesResult
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import use_cassette_and_stub_time_sleep_native


COUNT = 120


class TestFetchMessages:
    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/fetch_messages/max_100_single.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub'])
    def test_fetch_messages_return_max_100_for_single_channel(self):
        ch = "fetch-messages-ch-1"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "fetch-messages-uuid"

        for i in range(COUNT):
            envelope = pubnub.publish().channel(ch).message("hey-%s" % i).sync()
            assert isinstance(envelope.result, PNPublishResult)
            assert envelope.result.timetoken > 0

        while True:
            time.sleep(1)
            if len(pubnub.history().channel(ch).count(COUNT).sync().result.messages) >= 100:
                break

        envelope = pubnub.fetch_messages().channels(ch).sync()

        assert envelope is not None
        assert isinstance(envelope.result, PNFetchMessagesResult)
        assert len(envelope.result.channels[ch]) == 100

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/fetch_messages/max_25_multiple.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub'])
    def test_fetch_messages_return_max_25_for_multiple_channels(self):
        ch1 = "fetch-messages-ch-1"
        ch2 = "fetch-messages-ch-2"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "fetch-messages-uuid"

        for i in range(COUNT):
            envelope1 = pubnub.publish().channel(ch1).message("hey-%s" % i).sync()
            assert isinstance(envelope1.result, PNPublishResult)
            assert envelope1.result.timetoken > 0
            envelope2 = pubnub.publish().channel(ch2).message("hey-%s" % i).sync()
            assert isinstance(envelope2.result, PNPublishResult)
            assert envelope2.result.timetoken > 0

        while True:
            time.sleep(1)
            if len(pubnub.history().channel(ch1).count(COUNT).sync().result.messages) >= 100 and \
               len(pubnub.history().channel(ch2).count(COUNT).sync().result.messages) >= 100:
                break

        envelope = pubnub.fetch_messages().channels([ch1, ch2]).sync()

        assert isinstance(envelope.result, PNFetchMessagesResult)
        assert len(envelope.result.channels[ch1]) == 25
        assert len(envelope.result.channels[ch2]) == 25

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/fetch_messages/max_25_with_actions.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub'])
    def test_fetch_messages_actions_return_max_25(self):
        ch = "fetch-messages-actions-ch-1"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "fetch-messages-uuid"

        for i in range(COUNT):
            envelope = pubnub.publish().channel(ch).message("hey-%s" % i).sync()
            assert isinstance(envelope.result, PNPublishResult)
            assert envelope.result.timetoken > 0

        while True:
            time.sleep(1)
            if len(pubnub.history().channel(ch).count(COUNT).sync().result.messages) >= 100:
                break

        envelope = pubnub.fetch_messages().channels(ch).include_message_actions(True).sync()

        assert envelope is not None
        assert isinstance(envelope.result, PNFetchMessagesResult)
        assert len(envelope.result.channels[ch]) == 25

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/fetch_messages/include_meta.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub'])
    def test_fetch_messages_actions_include_meta(self):
        ch = "fetch-messages-actions-meta-1"
        pubnub = PubNub(pnconf_copy())
        pubnub.config.uuid = "fetch-messages-uuid"

        pubnub.publish().channel(ch).message("hey-meta").meta({"is-this": "krusty-krab"}).sync()
        pubnub.publish().channel(ch).message("hey-meta").meta({"this-is": "patrick"}).sync()

        envelope = pubnub.fetch_messages().channels(ch).include_message_actions(True).include_meta(True).sync()

        assert envelope is not None
        assert isinstance(envelope.result, PNFetchMessagesResult)
        history = envelope.result.channels[ch]
        assert len(history) == 2
        assert history[0].meta == {"is-this": "krusty-krab"}
        assert history[1].meta == {'this-is': 'patrick'}

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/fetch_messages/include_uuid.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub'])
    def test_fetch_messages_actions_include_uuid(self):
        ch = "fetch-messages-actions-uuid"
        pubnub = PubNub(pnconf_copy())
        uuid1 = "fetch-messages-uuid-1"
        uuid2 = "fetch-messages-uuid-2"

        pubnub.config.uuid = uuid1
        pubnub.publish().channel(ch).message("hey-uuid-1").sync()
        pubnub.config.uuid = uuid2
        pubnub.publish().channel(ch).message("hey-uuid-2").sync()
        time.sleep(1)
        envelope = pubnub.fetch_messages().channels(ch).include_message_actions(True).include_uuid(True).sync()

        assert envelope is not None
        assert isinstance(envelope.result, PNFetchMessagesResult)
        history = envelope.result.channels[ch]
        assert len(history) == 2
        assert history[0].uuid == uuid1
        assert history[1].uuid == uuid2

    @use_cassette_and_stub_time_sleep_native(
        'tests/integrational/fixtures/native_sync/fetch_messages/include_message_type.yaml',
        filter_query_parameters=['uuid', 'pnsdk', 'l_pub'])
    def test_fetch_messages_actions_include_message_type(self):
        ch = "fetch-messages-types"
        pubnub = PubNub(pnconf_copy())

        pubnub.config.uuid = "fetch-message-types"

        pubnub.publish().channel(ch).message("hey-type").sync()
        time.sleep(1)
        envelope = pubnub.fetch_messages().channels(ch).include_message_actions(True).include_message_type(True).sync()

        assert envelope is not None
        assert isinstance(envelope.result, PNFetchMessagesResult)
        history = envelope.result.channels[ch]
        assert len(history) == 1
        assert history[0].message_type == '1'
