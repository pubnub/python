from pubnub.managers import TelemetryManager
from pubnub.enums import PNOperationType


def test_average_latency():
    manager = TelemetryManager()
    endpointLatencies = [
        {"d": 100, "l": 10},
        {"d": 100, "l": 20},
        {"d": 100, "l": 30},
        {"d": 100, "l": 40},
        {"d": 100, "l": 50},
    ]

    averageLatency = manager.average_latency_from_data(endpointLatencies)

    assert 30 == averageLatency


def test_valid_queries():
    manager = TelemetryManager()

    manager.store_latency(1, PNOperationType.PNPublishOperation)
    manager.store_latency(2, PNOperationType.PNPublishOperation)
    manager.store_latency(3, PNOperationType.PNPublishOperation)
    manager.store_latency(4, PNOperationType.PNHistoryOperation)
    manager.store_latency(5, PNOperationType.PNHistoryOperation)
    manager.store_latency(6, PNOperationType.PNHistoryOperation)
    manager.store_latency(7, PNOperationType.PNRemoveGroupOperation)
    manager.store_latency(8, PNOperationType.PNRemoveGroupOperation)
    manager.store_latency(9, PNOperationType.PNRemoveGroupOperation)

    queries = manager.operation_latencies()

    assert queries['l_pub'] == 2
    assert queries['l_hist'] == 5
    assert queries['l_cg'] == 8
