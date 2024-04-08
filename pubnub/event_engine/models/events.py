from pubnub.exceptions import PubNubException
from typing import List, Optional


class PNEvent:
    def get_name(self) -> str:
        return self.__class__.__name__


class PNFailureEvent(PNEvent):
    def __init__(self, reason: PubNubException, attempt: int, timetoken: int = 0) -> None:
        self.reason = reason
        self.attempt = attempt
        self.timetoken = timetoken
        super().__init__()


class PNCursorEvent(PNEvent):
    def __init__(self, timetoken: str, region: Optional[int] = None, **kwargs) -> None:
        self.timetoken = timetoken
        self.region = region


class PNChannelGroupsEvent(PNEvent):
    def __init__(self, channels: List[str], groups: List[str]) -> None:
        self.channels = channels
        self.groups = groups


class SubscriptionChangedEvent(PNChannelGroupsEvent):
    def __init__(self, channels: List[str], groups: List[str], with_presence: Optional[bool] = None) -> None:
        PNChannelGroupsEvent.__init__(self, channels, groups)
        self.with_presence = with_presence


class SubscriptionRestoredEvent(PNCursorEvent, PNChannelGroupsEvent):
    def __init__(self, timetoken: str, channels: List[str], groups: List[str], region: Optional[int] = None,
                 with_presence: Optional[bool] = None) -> None:
        PNCursorEvent.__init__(self, timetoken, region)
        PNChannelGroupsEvent.__init__(self, channels, groups)
        self.with_presence = with_presence


class HandshakeSuccessEvent(PNCursorEvent):
    def __init__(self, timetoken: str, region: Optional[int] = None, **kwargs) -> None:
        super().__init__(timetoken, region)


class HandshakeFailureEvent(PNFailureEvent):
    pass


class HandshakeReconnectSuccessEvent(PNCursorEvent):
    pass


class HandshakeReconnectFailureEvent(PNFailureEvent):
    pass


class HandshakeReconnectGiveupEvent(PNFailureEvent):
    pass


class HandshakeReconnectRetryEvent(PNEvent):
    pass


class ReceiveSuccessEvent(PNCursorEvent):
    def __init__(self, timetoken: str, messages: list, region: Optional[int] = None) -> None:
        PNCursorEvent.__init__(self, timetoken, region)
        self.messages = messages


class ReceiveFailureEvent(PNFailureEvent):
    pass


class ReceiveReconnectSuccessEvent(PNCursorEvent):
    def __init__(self, timetoken: str, messages: list, region: Optional[int] = None) -> None:
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


class UnsubscribeAllEvent(PNEvent):
    pass


"""
    Presence Events
"""


class HeartbeatJoinedEvent(PNChannelGroupsEvent):
    pass


class HeartbeatReconnectEvent(PNEvent):
    pass


class HeartbeatLeftAllEvent(PNEvent):
    def __init__(self, suppress_leave: bool = False) -> None:
        self.suppress_leave = suppress_leave


class HeartbeatLeftEvent(PNChannelGroupsEvent):
    def __init__(self, channels: List[str], groups: List[str], suppress_leave: bool = False) -> None:
        PNChannelGroupsEvent.__init__(self, channels, groups)
        self.suppress_leave = suppress_leave


class HeartbeatDisconnectEvent(PNChannelGroupsEvent):
    pass


class HeartbeatSuccessEvent(PNChannelGroupsEvent):
    pass


class HeartbeatFailureEvent(PNChannelGroupsEvent, PNFailureEvent):
    def __init__(self, channels: List[str], groups: List[str], reason: PubNubException, attempt: int,
                 timetoken: int = 0) -> None:
        PNChannelGroupsEvent.__init__(self, channels, groups)
        PNFailureEvent.__init__(self, reason, attempt, timetoken)


class HeartbeatTimesUpEvent(PNEvent):
    pass


class HeartbeatGiveUpEvent(PNChannelGroupsEvent, PNFailureEvent):
    def __init__(self, channels: List[str], groups: List[str], reason: PubNubException, attempt: int,
                 timetoken: int = 0) -> None:
        PNChannelGroupsEvent.__init__(self, channels, groups)
        PNFailureEvent.__init__(self, reason, attempt, timetoken)
