"""
Placed into the separate file to avoid python <3.4 tests using it
"""
import six

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
