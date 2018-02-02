import logging

import tornado
from tornado.concurrent import Future
from tornado.testing import AsyncTestCase

import pubnub as pn
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope
from tests.helper import pnconf, pnconf_enc, gen_decrypt_func, pnconf_pam_copy
from tests.integrational.vcr_helper import pn_vcr

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "tornado-publish"


class TestPubNubAsyncPublish(AsyncTestCase):
    def setUp(self):
        AsyncTestCase.setUp(self)
        self.env = None

    def callback(self, tornado_res):
        self.env = tornado_res.result()
        self.pubnub.stop()
        self.stop()

    def assert_success(self, pub):
        pub.future().add_done_callback(self.callback)

        self.pubnub.start()
        self.wait()

        assert isinstance(self.env, TornadoEnvelope)
        assert isinstance(self.env.result, PNPublishResult)
        assert isinstance(self.env.status, PNStatus)
        assert self.env.result.timetoken > 0
        assert len(self.env.status.original_response) > 0

    @tornado.testing.gen_test
    def assert_success_yield(self, pub):
        envelope = yield pub.future()

        assert isinstance(envelope, TornadoEnvelope)
        assert isinstance(envelope.result, PNPublishResult)
        assert isinstance(envelope.status, PNStatus)
        assert envelope.result.timetoken > 0
        assert len(envelope.status.original_response) > 0

    def assert_success_publish_get(self, msg):
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)
        self.assert_success(self.pubnub.publish().channel(ch).message(msg))
        self.assert_success_yield(self.pubnub.publish().channel(ch).message(msg))

    def assert_success_publish_post(self, msg):
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)
        self.assert_success(self.pubnub.publish().channel(ch).message(msg).use_post(True))
        self.assert_success_yield(self.pubnub.publish().channel(ch).message(msg).use_post(True))

    def assert_success_publish_get_encrypted(self, msg):
        self.pubnub = PubNubTornado(pnconf_enc, custom_ioloop=self.io_loop)
        self.assert_success(self.pubnub.publish().channel(ch).message(msg))
        self.assert_success_yield(self.pubnub.publish().channel(ch).message(msg))

    def assert_success_publish_post_encrypted(self, msg):
        self.pubnub = PubNubTornado(pnconf_enc, custom_ioloop=self.io_loop)
        self.assert_success(self.pubnub.publish().channel(ch).message(msg).use_post(True))
        self.assert_success_yield(self.pubnub.publish().channel(ch).message(msg).use_post(True))

    def assert_client_side_error(self, pub, expected_err_msg):
        try:
            yield pub.future()

            self.pubnub.start()
            self.wait()
        except PubNubException as e:
            assert expected_err_msg in str(e)

        self.pubnub.stop()
        self.stop()

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/mixed_via_get.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'])
    def test_publish_mixed_via_get(self):
        self.assert_success_publish_get("hi")
        self.assert_success_publish_get(5)
        self.assert_success_publish_get(True)
        self.assert_success_publish_get(["hi", "hi2", "hi3"])

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/object_via_get.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'],
        match_on=['method', 'scheme', 'host', 'port', 'object_in_path', 'query'])
    def test_publish_object_via_get(self):
        self.assert_success_publish_get({"name": "Alex", "online": True})

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/mixed_via_post.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'],
        match_on=['method', 'scheme', 'host', 'port', 'path', 'query'])
    def test_publish_mixed_via_post(self):
        self.assert_success_publish_post("hi")
        self.assert_success_publish_post(5)
        self.assert_success_publish_post(True)
        self.assert_success_publish_post(["hi", "hi2", "hi3"])

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/object_via_post.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'],
        match_on=['host', 'method', 'path', 'query', 'object_in_body'])
    def test_publish_object_via_post(self):
        self.assert_success_publish_post({"name": "Alex", "online": True})

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/mixed_via_get_encrypted.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'])
    def test_publish_mixed_via_get_encrypted(self):
        self.assert_success_publish_get_encrypted("hi")
        self.assert_success_publish_get_encrypted(5)
        self.assert_success_publish_get_encrypted(True)
        self.assert_success_publish_get_encrypted(["hi", "hi2", "hi3"])

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/object_via_get_encrypted.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'],
        match_on=['host', 'method', 'query', 'object_in_path'],
        match_on_kwargs={'object_in_path': {
            'decrypter': gen_decrypt_func('testKey')}})
    def test_publish_object_via_get_encrypted(self):
        self.assert_success_publish_get_encrypted({"name": "Alex", "online": True})

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/mixed_via_post_encrypted.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'],
        match_on=['method', 'path', 'query', 'body'])
    def test_publish_mixed_via_post_encrypted(self):
        self.assert_success_publish_post_encrypted("hi")
        self.assert_success_publish_post_encrypted(5)
        self.assert_success_publish_post_encrypted(True)
        self.assert_success_publish_post_encrypted(["hi", "hi2", "hi3"])

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/object_via_post_encrypted.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'],
        match_on=['method', 'path', 'query', 'object_in_body'],
        match_on_kwargs={'object_in_body': {
            'decrypter': gen_decrypt_func('testKey')}})
    def test_publish_object_via_post_encrypted(self):
        self.assert_success_publish_post_encrypted({"name": "Alex", "online": True})

    def test_error_missing_message(self):
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

        self.assert_client_side_error(self.pubnub.publish().channel(ch).message(None), "Message missing")

    def test_error_missing_channel(self):
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

        self.assert_client_side_error(self.pubnub.publish().channel("").message("hey"), "Channel missing")

    def test_error_non_serializable(self):
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

        def method():
            pass

        self.assert_client_side_error(self.pubnub.publish().channel(ch).message(method), "not JSON serializable")

    def sserr_cb(self, env):
        assert isinstance(env, Future)
        exception = env.exception()

        self.pubnub.stop()
        # this kind of assertion will not fail the test if'll be moved below `self.stop()` call
        # but also not raises correct exception, timeout exception will be raised on fail instead
        assert self.expected_err_msg in str(exception)
        self.stop()

    def assert_server_side_error(self, pub, expected_err_msg):
        self.expected_err_msg = expected_err_msg
        pub.result().add_done_callback(self.sserr_cb)

        self.pubnub.start()
        self.wait()

    @tornado.testing.gen_test
    def assert_server_side_error_yield(self, pub, expected_err_msg):

        try:
            yield pub.result()

            self.pubnub.start()
            self.wait()
        except PubNubException as e:
            assert expected_err_msg in str(e)

        self.pubnub.stop()
        self.stop()

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/invalid_key.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'])
    def test_error_invalid_key(self):
        conf = PNConfiguration()
        conf.publish_key = "fake"
        conf.subscribe_key = "demo"

        self.pubnub = PubNubTornado(conf, custom_ioloop=self.io_loop)

        self.assert_server_side_error(self.pubnub.publish().channel(ch).message("hey"), "Invalid Key")
        self.assert_server_side_error_yield(self.pubnub.publish().channel(ch).message("hey"), "Invalid Key")

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/not_permitted.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'])
    def test_error_not_permitted_403(self):
        my_pnconf = pnconf_pam_copy()
        my_pnconf.secret_key = None
        self.pubnub = PubNubTornado(my_pnconf, custom_ioloop=self.io_loop)

        self.assert_server_side_error(
            self.pubnub.publish().channel("not_permitted_channel").message("hey"), "HTTP Client Error (403)")
        self.assert_server_side_error_yield(
            self.pubnub.publish().channel("not_permitted_channel").message("hey"), "HTTP Client Error (403)")

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/meta_object.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'],
        match_on=['host', 'method', 'path', 'meta_object_in_query'])
    def test_publish_with_meta(self):
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

        self.assert_success(
            self.pubnub.publish().channel(ch).message("hey").meta({'a': 2, 'b': 'qwer'}))
        self.assert_success_yield(
            self.pubnub.publish().channel(ch).message("hey").meta({'a': 2, 'b': 'qwer'}))

    @pn_vcr.use_cassette(
        'tests/integrational/fixtures/tornado/publish/do_not_store.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk', 'l_pub'])
    def test_publish_do_not_store(self):
        self.pubnub = PubNubTornado(pnconf, custom_ioloop=self.io_loop)

        self.assert_success(
            self.pubnub.publish().channel(ch).message("hey").should_store(False))
        self.assert_success_yield(
            self.pubnub.publish().channel(ch).message("hey").should_store(False))
