import unittest

from datetime import date

from pubnub.models.consumer.time import PNTimeResponse


class TestTime(unittest.TestCase):
    def test_parse(self):
        time = PNTimeResponse([14695274331639244])

        assert int(time) == 14695274331639244
        assert time.value_as_int == 14695274331639244

        assert str(time) == "14695274331639244"
        assert time.value_as_string == "14695274331639244"

        assert isinstance(time.date_time(), date)
