import unittest

from tests.integrational.vcr_helper import string_list_in_path_matcher, string_list_in_query_matcher


class Request(object):
    def __init__(self, path=None, query=None):
        self.path = path
        self.query = query


class TestVCRMatchers(unittest.TestCase):
    def test_string_list_in_path_matcher(self):
        r1 = Request('/v2/presence/sub-key/my_sub_key/channel/ch1,ch2')
        r2 = Request('/v2/presence/sub-key/my_sub_key/channel/ch2,ch1')
        r3 = Request('/v2/presence/sub-key/my_sub_key/channel/ch2,ch3')
        r4 = Request(
            '/v2/subscribe/sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe/test-here-now-asyncio-ch2,test-here-now-asyncio-ch1/0')  # noqa: E501
        r5 = Request(
            '/v2/subscribe/sub-c-33f55052-190b-11e6-bfbc-02ee2ddab7fe/test-here-now-asyncio-ch1,test-here-now-asyncio-ch2/0')  # noqa: E501

        assert string_list_in_path_matcher(r1, r2, 6)
        assert not string_list_in_path_matcher(r2, r3, 6)
        assert string_list_in_path_matcher(r4, r5, 4)
        assert not string_list_in_path_matcher(r4, r5)

    def test_string_list_in_path_query_matcher(self):
        r1 = Request(
            query=[('channel', 'test-pam-asyncio-ch1,test-pam-asyncio-ch2'), ('pnsdk', 'PubNub-Python-Asyncio/4.0.4'),
                   ('r', '1'), ('uuid', 'test-pam-asyncio-uuid'), ('w', '1')])
        r2 = Request(
            query=[('channel', 'test-pam-asyncio-ch2,test-pam-asyncio-ch1'), ('pnsdk', 'PubNub-Python-Asyncio/4.0.4'),
                   ('r', '1'), ('uuid', 'test-pam-asyncio-uuid'), ('w', '1')])

        assert string_list_in_query_matcher(r1, r2, ['channel'])
        assert not string_list_in_query_matcher(r1, r2)
