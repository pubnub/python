from functools import wraps
from vcr.errors import CannotOverwriteExistingCassetteException
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

    async def fake_sleeper(v):
        await asyncio.sleep(0)

    def decorate(f):
        @wraps(f)
        async def call(*args, event_loop=None):
            if not event_loop:
                event_loop = asyncio.get_event_loop()
            await f(*args, sleeper=(fake_sleeper if (len(cs) > 0) else asyncio.sleep), event_loop=event_loop)

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
    def __init__(self, raise_times):
        self.silent_limit = raise_times
        self.raised_times = 0

        super(VCR599Listener, self).__init__()

    async def _wait_for(self, coro):
        try:
            res = await super(VCR599Listener, self)._wait_for(coro)
            return res
        except CannotOverwriteExistingCassetteException as e:
            if "Can't overwrite existing cassette" in str(e):
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
