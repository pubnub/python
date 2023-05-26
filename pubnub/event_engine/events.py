from pubnub.exceptions import PubNubException


class PNEvent:
    def get_name(self) -> str:
        return self.__class__.__name__


class PNFailureEvent(PNEvent):
    def __init__(self, reason: PubNubException, attempt: int) -> None:
        self.reason = reason


class PNCursorEvent(PNEvent):
    def __init__(self, timetoken: str, region: int) -> None:
        self.timetoken = timetoken
        self.region = region


class PNChannelGroupsEvent(PNEvent):
    def __init__(self, channels: list[str], groups: list[str]) -> None:
        self.channels = channels
        self.groups = groups


class SubscriptionChangedEvent(PNChannelGroupsEvent):
    def __init__(self, channels: list[str], groups: list[str]) -> None:
        PNChannelGroupsEvent.__init__(self, channels, groups)


class SubscriptionRestoredEvent(PNCursorEvent, PNChannelGroupsEvent):
    def __init__(self, timetoken: str, region: int, channels: list[str], groups: list[str]) -> None:
        PNCursorEvent.__init__(self, timetoken, region)
        PNChannelGroupsEvent.__init__(self, channels, groups)


class HandshakeSuccessEvent(PNCursorEvent):
    def __init__(self, attempt: int, reason: PubNubException) -> None:
        self.attempt = attempt
        self.reason = reason


class HandshakeFailureEvent(PNFailureEvent):

    pass


class HandshakeReconnectSuccessEvent(PNCursorEvent):
    pass


class HandshakeReconnectFailureEvent(PNFailureEvent):
    pass


class HandshakeReconnectGiveupEvent(PNEvent):
    pass


class HandshakeReconnectRetryEvent(PNEvent):
    pass


class ReceiveSuccessEvent(PNCursorEvent):
    def __init__(self, timetoken: str, region: int, messages: list) -> None:
        PNCursorEvent.__init__(self, timetoken, region)
        self.messages = messages


class ReceiveFailureEvent(PNFailureEvent):
    pass


class ReceiveReconnectSuccessEvent(PNCursorEvent):
    def __init__(self, timetoken: str, region: int, messages: list) -> None:
        PNCursorEvent.__init__(self, timetoken, region)
        self.messages = messages


class ReceiveReconnectFailureEvent(PNFailureEvent):
    pass


class ReceiveReconnectGiveupEvent(PNFailureEvent):
    pass


class ReceiveReconnectRetryEvent(PNEvent):
    pass


class DisconnectEvent(PNEvent):
    pass


class ReconnectEvent(PNEvent):
    pass
