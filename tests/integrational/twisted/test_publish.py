from twisted.internet import defer
from twisted.internet.task import deferLater
from twisted.internet.tcp import Client
from twisted.internet import reactor
from twisted.trial import unittest
from twisted.web.client import HTTPConnectionPool

import logging
import pubnub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_twisted import PubNubTwisted
from tests.helper import pnconf

pubnub.set_stream_logger('pubnub', logging.DEBUG)
defer.setDebugging(True)

ch = "twisted-int-publish"


class TwistedTest(unittest.TestCase):
    def setUp(self):
        self.pool = HTTPConnectionPool(reactor, False)
        self.pubnub = PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)

    def tearDown(self):
        def _check_fds(_):
            fds = set(reactor.getReaders() + reactor.getReaders())
            if not [fd for fd in fds if isinstance(fd, Client)]:
                return
            return deferLater(reactor, 0, _check_fds, None)

        return self.pool.closeCachedConnections().addBoth(_check_fds)


class TestPubNubPublishSuccess(TwistedTest):
    def callback(self, res, third=None):
        print(res.timetoken)
        assert res.timetoken > 0

    def errback(self, error):
        return defer.fail(error)

    def assert_success(self, pub):
        d = defer.Deferred()
        pub.deferred().addCallback(self.callback, self.errback).addCallbacks(d.callback, d.errback)
        return d

    def assert_success_publish_get(self, msg):
        return self.assert_success(
            PubNubTwisted(pnconf, reactor=reactor, pool=self.pool).publish().channel(ch).message(msg))

    def assert_success_publish_post(self, msg):
        return self.assert_success(
            PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)
                .publish().channel(ch).message(msg).use_post(True))

    def test_success_publish_string_get(self):
        return self.assert_success_publish_get("hey")

    def test_success_publish_int_get(self):
        return self.assert_success_publish_get(5)

    def test_success_publish_bool_get(self):
        return self.assert_success_publish_get(True)

    def test_success_publish_list_get(self):
        return self.assert_success_publish_get(["hi", "hi2", "hi3"])

    def test_success_publish_dict_get(self):
        return self.assert_success_publish_get({"name": "Alex", "online": True})

    def test_success_publish_string_post(self):
        return self.assert_success_publish_get("hey")

    def test_success_publish_int_post(self):
        return self.assert_success_publish_get(5)

    def test_success_publish_bool_post(self):
        return self.assert_success_publish_get(True)

    def test_success_publish_list_post(self):
        return self.assert_success_publish_get(["hi", "hi2", "hi3"])

    def test_success_publish_dict_post(self):
        return self.assert_success_publish_get({"name": "Alex", "online": True})

    def test_success_publish_do_not_store(self):
        return self.assert_success(
            PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)
                .publish().channel(ch).message("hey").should_store(False))

    def test_success_publish_with_meta(self):
        return self.assert_success(
            PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)
                .publish().channel(ch).message("hey").meta({'a': 2, 'b': 'qwer'}))


class TestPubNubPublishError(TwistedTest):
    def callback(self, res, third=None):
        return defer.fail("Success while while is expected: " + str(res))

    def errback_message_missing(self, error):
        self.assertIn("Message missing", error.getErrorMessage())
        return defer.succeed(None)

    def errback_channel_missing(self, error):
        self.assertIn("Channel missing", error.getErrorMessage())
        return defer.succeed(None)

    def errback_non_serializable(self, error):
        self.assertIn("not JSON serializable", error.getErrorMessage())
        return defer.succeed(None)

    def errback_invalid_key(self, error):
        self.assertIn("HTTP Client Error (400)", error.getErrorMessage())
        self.assertIn("Invalid Key", error.getErrorMessage())
        return defer.succeed(None)

    def assert_error(self, pub, errback):
        d = defer.Deferred()
        pub.deferred()\
            .addCallbacks(self.callback, errback) \
            .addCallbacks(d.callback, d.errback)

        return d

    def test_error_missing_message(self):
        return self.assert_error(self.pubnub.publish().channel(ch).message(None),
                                 self.errback_message_missing)

    def test_error_missing_channel(self):
        return self.assert_error(self.pubnub.publish().channel("").message("hey"),
                                 self.errback_channel_missing)

    def test_error_non_serializable(self):
        def method():
            pass

        return self.assert_error(self.pubnub.publish().channel(ch).message(method),
                                 self.errback_non_serializable)

    def test_error_invalid_key(self):
        conf = PNConfiguration()
        conf.publish_key = "fake"
        conf.subscribe_key = "demo"
        self.pubnub = PubNubTwisted(conf, reactor=reactor, pool=self.pool)

        return self.assert_error(self.pubnub.publish().channel(ch).message("hey"),
                                 self.errback_invalid_key)
