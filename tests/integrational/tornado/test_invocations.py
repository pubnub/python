import logging
import pytest
import pubnub as pn
import tornado

from tests.integrational.tornado.vcr_tornado_decorator import use_cassette_and_stub_time_sleep

pn.set_stream_logger('pubnub', logging.DEBUG)

from tornado.testing import AsyncTestCase
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.pubsub import PNPublishResult
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_tornado import PubNubTornado, TornadoEnvelope, PubNubTornadoException
from tests.helper import pnconf_sub_copy

corrupted_keys = PNConfiguration()
corrupted_keys.publish_key = "blah"
corrupted_keys.subscribe_key = "blah"

pn.set_stream_logger('pubnub', logging.DEBUG)

ch = "tornado-publish"


class TestPubNubTornadoInvocations(AsyncTestCase):
    def setUp(self):
        super(TestPubNubTornadoInvocations, self).setUp()

    @tornado.testing.gen_test
    def test_publish_resultx(self):
        pubnub = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)
        result = yield pubnub.publish().message('hey').channel('blah').result()
        assert isinstance(result, PNPublishResult)

        pubnub.stop()

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/invocations/result_raises.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_publish_result_raises_pubnub_error(self):
        pubnub = PubNubTornado(corrupted_keys, custom_ioloop=self.io_loop)
        with pytest.raises(PubNubException) as exinfo:
            yield pubnub.publish().message('hey').channel('blah').result()

        assert 'Invalid Subscribe Key' in str(exinfo.value)
        assert 400 == exinfo.value._status_code

        pubnub.stop()

    @tornado.testing.gen_test
    def xtest_publish_result_raises_lower_level_error(self):
        pubnub = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)

        # TODO: find a better way ot emulate broken connection
        pubnub.http.close()

        with self.assertRaises(Exception) as context:
            yield pubnub.publish().message('hey').channel('blah').result()

        assert 'fetch() called on closed AsyncHTTPClient' in str(context.exception.message)

        pubnub.stop()

    @tornado.testing.gen_test
    def test_publish_futurex(self):
        pubnub = PubNubTornado(pnconf_sub_copy(), custom_ioloop=self.io_loop)
        envelope = yield pubnub.publish().message('hey').channel('blah').future()
        assert isinstance(envelope, TornadoEnvelope)
        assert not envelope.is_error()

        pubnub.stop()

    @use_cassette_and_stub_time_sleep(
        'tests/integrational/fixtures/tornado/invocations/future_raises.yaml',
        filter_query_parameters=['uuid', 'seqn', 'pnsdk'])
    @tornado.testing.gen_test
    def test_publish_future_raises(self):
        pubnub = PubNubTornado(corrupted_keys, custom_ioloop=self.io_loop)
        e = yield pubnub.publish().message('hey').channel('blah').future()
        assert isinstance(e, PubNubTornadoException)
        assert e.is_error()
        assert 400 == e.value()._status_code

        pubnub.stop()

    @tornado.testing.gen_test
    def xtest_publish_future_raises_lower_level_error(self):
        pubnub = PubNubTornado(corrupted_keys, custom_ioloop=self.io_loop)

        pubnub.http.close()

        e = yield pubnub.publish().message('hey').channel('blah').future()
        assert isinstance(e, PubNubTornadoException)
        assert str(e) == "fetch() called on closed AsyncHTTPClient"

        pubnub.stop()
