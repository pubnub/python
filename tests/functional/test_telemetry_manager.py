import time

from pubnub.managers import TelemetryManager
from pubnub.pubnub import NativeTelemetryManager
from pubnub.enums import PNOperationType


def test_cleaning_up_latency_data():
    manager = TelemetryManager()
    manager.MAXIMUM_LATENCY_DATA_AGE = 1

    for i in range(0, 10):
        manager.store_latency(i, PNOperationType.PNPublishOperation)

    # await for store timestamp expired
    time.sleep(2)

    manager.clean_up_telemetry_data()
    print(manager.latencies)

    assert len(manager.operation_latencies()) == 0


def test_native_telemetry_cleanup():
    manager = NativeTelemetryManager()
    manager.MAXIMUM_LATENCY_DATA_AGE = 1

    for i in range(1, 10):
        manager.store_latency(i, PNOperationType.PNPublishOperation)

    time.sleep(2)

    for i in range(1, 10):  # Latency = 0 is not being stored!
        manager.store_latency(i, PNOperationType.PNPublishOperation)

    assert len(manager.latencies["pub"]) == 9
