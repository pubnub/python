import unittest

from pubnub import utils
from pubnub.utils import build_url

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

try:
    from urllib.parse import parse_qs
except ImportError:
    from urlparse import parse_qs


class TestWriteValueAsString(unittest.TestCase):
    def test_string(self):
        assert utils.write_value_as_string("blah") == "\"blah\""
        assert utils.write_value_as_string(u"blah") == "\"blah\""

    def test_bool(self):
        assert utils.write_value_as_string(False) == "false"
        assert utils.write_value_as_string(True) == "true"

    def test_list(self):
        assert utils.write_value_as_string(["ch1", "ch2"]) == "[\"ch1\", \"ch2\"]"

    def test_tuple(self):
        assert utils.write_value_as_string(("ch1", "ch2")) == "[\"ch1\", \"ch2\"]"


class TestUUID(unittest.TestCase):
    def test_uuid(self):
        assert isinstance(utils.uuid(), str)
        assert len(utils.uuid()) == 36


class TestBuildUrl(unittest.TestCase):
    def test_build_url(self):
        def match(expected_str, actual_str):
            expected = urlparse(expected_str)
            actual = urlparse(actual_str)
            assert expected.scheme == actual.scheme
            assert expected.netloc == actual.netloc
            assert expected.path == actual.path
            self.assertEqual(parse_qs(expected.query), parse_qs(actual.query))

        match("http://ex.com/news?a=2&b=qwer",
              build_url("http", "ex.com", "/news", "a=2&b=qwer"))
        match("https://ex.com/?a=2&b=qwer",
              build_url("https", "ex.com", "/", "a=2&b=qwer"))


class TestJoin(unittest.TestCase):
    def test_join_items_and_encode(self):
        assert "a%2Fb,c%20d" == utils.join_items_and_encode(['a/b', 'c d'])


class TestPreparePAMArguments(unittest.TestCase):
    def test_prepare_pam_arguments(self):
        params = {
            'abc': True,
            'poq': 4,
            'def': False
        }

        result = utils.prepare_pam_arguments(params)
        assert result == 'abc=True&def=False&poq=4'

    def test_sign_sha_256(self):
        input = """sub-c-7ba2ac4c-4836-11e6-85a4-0619f8945a4f
pub-c-98863562-19a6-4760-bf0b-d537d1f5c582
grant
channel=asyncio-pam-FI2FCS0A&pnsdk=PubNub-Python-Asyncio%252F4.0.4&r=1&timestamp=1468409553&uuid=a4dbf92e-e5cb-428f-b6e6-35cce03500a2&w=1"""  # noqa: E501
        result = utils.sign_sha256("my_key", input)

        assert "zXtkplNSczgpsfhaYajoEfQnIgRTUCgE9AE6Y0mS_J8=" == result
