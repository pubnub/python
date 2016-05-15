import unittest

from pubnub import utils


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
