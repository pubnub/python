import logging
import unittest

import pubnub
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pubnub import PubNub
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr

pubnub.set_stream_logger('pubnub', logging.DEBUG)


class TestPubNubPublish(unittest.TestCase):
    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/ssl/ssl.yaml',
                         filter_query_parameters=['uuid', 'pnsdk'])
    def test_publish_string_get(self):
        pnconf = pnconf_copy()
        pnconf.ssl = True
        try:
            env = PubNub(pnconf).publish() \
                .channel("ch1") \
                .message("hi") \
                .sync()

            assert isinstance(env.result, PNPublishResult)
            assert env.result.timetoken > 1
        except PubNubException as e:
            self.fail(e)
