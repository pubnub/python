import unittest
import time

from pubnub.managers import TelemetryManager
from pubnub.enums import PNOperationType


class TestTelemetryManager(unittest.TestCase):  # pylint: disable=W0612
    @classmethod
    def test_clean_up(cls):
        manager = TelemetryManager()
        manager.MAXIMUM_LATENCY_DATA_AGE = 1

        for i in range(0, 10):
            manager.store_latency(i, PNOperationType.PNPublishOperation)

        # await for store timestamp expired
        time.sleep(2)

        manager.clean_up_telemetry_data()
        print(manager.latencies)

        if not 0 == len(manager.operation_latencies()):
            raise AssertionError()
