import json
import os
import six
import vcr
try:
    from mock import patch
except ImportError:
    from unittest.mock import patch

from tests.helper import url_decode

vcr_dir = os.path.dirname(os.path.dirname((os.path.dirname(os.path.abspath(__file__)))))

pn_vcr = vcr.VCR(
    cassette_library_dir=vcr_dir
)


def meta_object_in_query_matcher(r1, r2):
    return assert_request_equal_with_object_in_query(r1, r2, 'meta')


def state_object_in_query_matcher(r1, r2):
    return assert_request_equal_with_object_in_query(r1, r2, 'state')


def assert_request_equal_with_object_in_query(r1, r2, query_field_name):
    try:
        for v in r1.query:
            if v[0] == query_field_name:
                for w in r2.query:
                    if w[0] == query_field_name:
                        assert json.loads(v[1]) == json.loads(w[1])
            else:
                for w in r2.query:
                    if w[0] == v[0]:
                        assert w[1] == v[1]

    except AssertionError:
        return False

    return True


def object_in_path_matcher(r1, r2, decrypter=None):
    try:
        path1 = r1.path.split('/')
        path2 = r2.path.split('/')

        for k, v in enumerate(path1):
            if k == (len(path1) - 1):
                if decrypter is not None:
                    assert decrypter(url_decode(v)) == decrypter(url_decode(path2[k]))
                else:
                    assert json.loads(url_decode(v)) == json.loads(url_decode(path2[k]))
            else:
                assert v == path2[k]

    except AssertionError:
        return False

    return True


def object_in_body_matcher(r1, r2, decrypter=None):
    try:
        if decrypter is not None:
            assert decrypter(r1.body.decode('utf-8')) == decrypter(r2.body.decode('utf-8'))
        else:
            assert json.loads(url_decode(r1.body.decode('utf-8'))) == json.loads(url_decode(r2.body.decode('utf-8')))

    except AssertionError:
        return False

    return True


def string_list_in_path_matcher(r1, r2, positions=None):
    """
    For here_now requests:
    /v2/presence/sub-key/my_sub_key/channel/ch1,ch2?key=val
    /v2/presence/sub-key/my_sub_key/channel/ch2,ch1?key=val
    """

    if positions is None:
        positions = []
    elif isinstance(positions, six.integer_types):
        positions = [positions]

    try:
        path1 = r1.path.split('/')
        path2 = r2.path.split('/')

        for k, v in enumerate(path1):
            if k in positions:
                ary1 = v.split(',')
                ary1.sort()
                ary2 = path2[k].split(',')
                ary2.sort()

                assert ary1 == ary2
            else:
                assert v == path2[k]

    except (AssertionError, IndexError):
        return False
    except Exception as e:
        print("Non-Assertion Exception: %s" % e)
        raise

    return True


def string_list_in_query_matcher(r1, r2, list_keys=None, filter_keys=None):
    """
    For here_now requests:

    /v1/auth/grant/sub-key/my_sub_key?channel=ch1,ch2&timestamp=123
    /v1/auth/grant/sub-key/my_sub_key?channel=ch2,ch1&timestamp=124

    NOTICE: The :filter_query_parameters: cassette param should be specified alongside with :filter_keys:
    """

    if list_keys is None:
        list_keys = []
    elif isinstance(list_keys, six.string_types):
        list_keys = [list_keys]

    if filter_keys is None:
        filter_keys = []
    elif isinstance(filter_keys, six.string_types):
        filter_keys = [filter_keys]

    try:
        list1 = r1.query
        list2 = r2.query

        for ik, tp in enumerate(list1):
            k, v = tp
            if k in filter_keys:
                continue

            if k in list_keys:
                ary1 = v.split(',')
                ary1.sort()
                ary2 = list2[ik][1].split(',')
                ary2.sort()

                assert ary1 == ary2
            else:
                assert v == list2[ik][1]

    except (AssertionError, IndexError):
        return False
    except Exception as e:
        print("Non-Assertion Exception: %s" % e)
        raise

    return True


def check_the_difference_matcher(r1, r2):
    """ A helper to check the difference between two requests """

    try:
        assert r1.body == r2.body
        assert r1.headers == r2.headers
        assert r1.host == r2.host
        assert r1.method == r2.method
        assert r1.query == r2.query
        assert r1.port == r2.port
        assert r1.protocol == r2.protocol
        assert r1.scheme == r2.scheme
        assert r1.path == r2.path
    except AssertionError:
        return False

    return True


pn_vcr.register_matcher('meta_object_in_query', meta_object_in_query_matcher)
pn_vcr.register_matcher('state_object_in_query', state_object_in_query_matcher)
pn_vcr.register_matcher('object_in_path', object_in_path_matcher)
pn_vcr.register_matcher('object_in_body', object_in_body_matcher)
pn_vcr.register_matcher('check_the_difference', check_the_difference_matcher)
pn_vcr.register_matcher('string_list_in_path', string_list_in_path_matcher)
pn_vcr.register_matcher('string_list_in_query', string_list_in_query_matcher)


def use_cassette_and_stub_time_sleep_native(cassette_name, **kwargs):
    context = pn_vcr.use_cassette(cassette_name, **kwargs)
    full_path = "{0}/{1}".format(pn_vcr.cassette_library_dir, cassette_name)
    cs = context.cls(path=full_path).load(path=full_path)

    def _inner(f):
        @patch('time.sleep', return_value=None)
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
