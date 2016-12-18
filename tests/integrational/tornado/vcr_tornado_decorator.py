import six

from tests.integrational.vcr_helper import pn_vcr

try:
    from mock import patch
except ImportError:
    from unittest.mock import patch


def use_cassette_and_stub_time_sleep(cassette_name, **kwargs):
    context = pn_vcr.use_cassette(cassette_name, **kwargs)
    full_path = "{}/{}".format(pn_vcr.cassette_library_dir, cassette_name)
    cs = context.cls(path=full_path).load(path=full_path)

    if 'filter_query_parameters' in kwargs:
        kwargs['filter_query_parameters'].append('pnsdk')

    import tornado.gen

    @tornado.gen.coroutine
    def returner():
        return

    def _inner(f):
        @patch('tornado.gen.sleep', return_value=returner())
        @six.wraps(f)
        def stubbed(*args, **kwargs):
            with context:
                largs = list(args)
                # 1 - index
                largs.pop(1)
                return f(*largs, **kwargs)

        @six.wraps(f)
        def original(*args):
            with context:
                return f(*args)

        return stubbed if len(cs) > 0 else original

    return _inner
