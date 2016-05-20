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
                     build_url("http", "ex.com", "/news", {"a": 2, "b": "qwer"}))
        match("https://ex.com/?a=2&b=qwer",
                     build_url("https", "ex.com", "/", {"a": 2, "b": "qwer"}))

