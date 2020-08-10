from pubnub.managers import TelemetryManager
from pubnub.enums import PNOperationType


def test_average_latency():
    manager = TelemetryManager()
    endpointLatencies = [
        {"timestamp": 100, "latency": 10},
        {"timestamp": 100, "latency": 20},
        {"timestamp": 100, "latency": 30},
        {"timestamp": 100, "latency": 40},
        {"timestamp": 100, "latency": 50},
    ]

    averageLatency = manager.average_latency_from_data(endpointLatencies)

    if not 30 == averageLatency:
        raise AssertionError()


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

    if not queries['l_pub'] == 2:
        raise AssertionError()
    if not queries['l_hist'] == 5:
        raise AssertionError()
    if not queries['l_cg'] == 8:
        raise AssertionError()
