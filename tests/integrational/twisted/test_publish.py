from twisted.internet import defer
from twisted.internet.task import deferLater
from twisted.internet.tcp import Client
from twisted.internet import reactor
from twisted.trial import unittest
from twisted.web.client import HTTPConnectionPool

import logging
import pubnub
from pubnub.pubnub_twisted import PubNubTwisted
from tests.helper import pnconf

pubnub.set_stream_logger('pubnub', logging.DEBUG)
defer.setDebugging(True)


class TestPubNubPublish(unittest.TestCase):
    def setUp(self):
            self.pool = HTTPConnectionPool(reactor, False)

    def tearDown(self):
        def _check_fds(_):
            fds = set(reactor.getReaders() + reactor.getReaders())
            if not [fd for fd in fds if isinstance(fd, Client)]:
                return
            return deferLater(reactor, 0, _check_fds, None)

        return self.pool.closeCachedConnections().addBoth(_check_fds)

    def success(self, res, third=None):
        print(res.timetoken)
        assert res.timetoken > 0

    def error(self, error):
        return defer.fail(error)

    def test_publish_deferred(self):
        d = defer.Deferred()

        pubnub = PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)

        pubnub.publish() \
            .channel("my_channel") \
            .message("deferred hello using GET") \
            .deferred() \
            .addCallback(self.success) \
            .addCallbacks(d.callback, d.errback)

        return d

    def test_publish_sync(self):
        pubnub = PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)

        res = pubnub.publish() \
            .channel("my_channel") \
            .message("sync hello using GET") \
            .sync()

        assert res.timetoken > 0

    def test_publish_list_deferred(self):
        d = defer.Deferred()

        pubnub = PubNubTwisted(pnconf, reactor=reactor, pool=self.pool)

        pubnub.publish() \
            .channel("my_channel") \
            .message(["deferred", "hello", "using", "GET"]) \
            .deferred() \
            .addCallback(self.success) \
            .addCallbacks(d.callback, d.errback)

        return d

    def test_publish_post_deferred(self):
        d = defer.Deferred()

        # delayedCall = reactor.callLater(3, d.cancel)
        #
        # def gotResult(result):
        #     if delayedCall.active():
        #         delayedCall.cancel()
        #     return result

        PubNubTwisted(pnconf, reactor=reactor, pool=self.pool).publish() \
            .channel("my_channel") \
            .message("deferred string hello using POST") \
            .use_post(True) \
            .deferred() \
            .addCallback(self.success, self.error) \
            .addCallbacks(d.callback, d.errback)
            # .addBoth(gotResult)

        return d

    def test_publish_post_list_deferred(self):
        d = defer.Deferred()

        PubNubTwisted(pnconf, reactor=reactor, pool=self.pool).publish() \
            .channel("my_channel") \
            .message(["deferred", "list", "using", "POST"]) \
            .use_post(True) \
            .deferred() \
            .addCallback(self.success, self.error) \
            .addCallbacks(d.callback, d.errback)

        return d
