"""
Placed into the separate file to avoid python <3.4 tests using it
"""
import six

from pubnub.exceptions import PubNubException
from pubnub.pubnub_asyncio import SubscribeListener, AsyncioReconnectionManager

from tests.integrational.vcr_helper import pn_vcr


def get_sleeper(cassette_name):
    """
    Loads cassette just to check if it is in record or playback mode
    """
    context = pn_vcr.use_cassette(cassette_name)
    full_path = "{}/{}".format(pn_vcr.cassette_library_dir, cassette_name)
    cs = context.cls(path=full_path).load(path=full_path)

    import asyncio

    @asyncio.coroutine
    def fake_sleeper(v):
        yield from asyncio.sleep(0)

    def decorate(f):
        @six.wraps(f)
        def call(*args, event_loop=None):
            yield from f(*args, sleeper=(fake_sleeper if (len(cs) > 0) else asyncio.sleep), event_loop=event_loop)

        return call
    return decorate


class VCR599Listener(SubscribeListener):
    """
     The wrapper for SubscribeListener.

     Provides option to ignore the certain amount of 599 VCR errors.

     599 VCR errors can be undesirable raised in case when the request
     was not recorded since it was in long-polling phase at the time when
     the test was finished.

     This means if you use this listener you should determine the amount
     of 599 errors can be raised by you own and explicitly pass it to constructor.
     """

    import asyncio

    def __init__(self, raise_times):
        self.silent_limit = raise_times
        self.raised_times = 0

        super(VCR599Listener, self).__init__()

    @asyncio.coroutine
    def _wait_for(self, coro):
        try:
            res = yield from super(VCR599Listener, self)._wait_for(coro)
            return res
        except PubNubException as e:
            if 'HTTP Server Error (599)' in str(e):
                self.raised_times += 1
                if self.raised_times > self.silent_limit:
                    raise e
                else:
                    """ HACK: case assumes that this is a long-polling request that wasn't fulfilled
                    at the time when it was recorded. To simulate this a sleep method was used.
                    """
                    pass
                    # yield from asyncio.sleep(1000)
            else:
                raise


class VCR599ReconnectionManager(AsyncioReconnectionManager):
    def __init__(self, pubnub):
        super(VCR599ReconnectionManager, self).__init__(pubnub)

    def start_polling(self):
        print(">>> Skip polling after 599 Error")

    def stop_polling(self):
        pass
