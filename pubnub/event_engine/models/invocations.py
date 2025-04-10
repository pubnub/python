from typing import List, Optional, Union
from pubnub.exceptions import PubNubException
from pubnub.enums import PNOperationType, PNStatusCategory


class PNInvocation:
    pass


class PNManageableInvocation(PNInvocation):
    pass


class PNCancelInvocation(PNInvocation):
    cancel_effect: str


class HandshakeInvocation(PNManageableInvocation):
    def __init__(self, channels: Union[None, List[str]] = None, groups: Union[None, List[str]] = None,
                 timetoken: Union[None, int] = None) -> None:
        super().__init__()
        self.channels = channels
        self.groups = groups
        self.timetoken = timetoken


class CancelHandshakeInvocation(PNCancelInvocation):
    cancel_effect = HandshakeInvocation.__name__


class ReceiveMessagesInvocation(PNManageableInvocation):
    def __init__(self,
                 channels: Union[None, List[str]] = None,
                 groups: Union[None, List[str]] = None,
                 timetoken: Union[None, str] = None,
                 region: Union[None, int] = None
                 ) -> None:
        super().__init__()
        self.channels = channels
        self.groups = groups
        self.timetoken = timetoken
        self.region = region


class CancelReceiveMessagesInvocation(PNCancelInvocation):
    cancel_effect = ReceiveMessagesInvocation.__name__


class ReconnectInvocation(PNManageableInvocation):
    def __init__(self,
                 channels: Union[None, List[str]] = None,
                 groups: Union[None, List[str]] = None,
                 timetoken: Union[None, str] = None,
                 region: Union[None, int] = None,
                 attempts: Union[None, int] = None,
                 reason: Union[None, PubNubException] = None
                 ) -> None:
        self.channels = channels
        self.groups = groups
        self.attempts = attempts
        self.reason = reason
        self.timetoken = timetoken
        self.region = region


class HandshakeReconnectInvocation(ReconnectInvocation):
    pass


class CancelHandshakeReconnectInvocation(PNCancelInvocation):
    cancel_effect = HandshakeReconnectInvocation.__name__


class ReceiveReconnectInvocation(ReconnectInvocation):
    pass


class CancelReceiveReconnectInvocation(PNCancelInvocation):
    cancel_effect = ReceiveReconnectInvocation.__name__


class PNEmittableInvocation(PNInvocation):
    pass


class EmitMessagesInvocation(PNEmittableInvocation):
    def __init__(self, messages: Union[None, List[str]]) -> None:
        super().__init__()
        self.messages = messages


class EmitStatusInvocation(PNEmittableInvocation):
    def __init__(
            self,
            status: Optional[PNStatusCategory],
            operation: Optional[PNOperationType] = None,
            context=None,
    ) -> None:
        super().__init__()
        self.status = status
        self.operation = operation
        self.context = context


"""
    Presence Effects
"""


class HeartbeatInvocation(PNManageableInvocation):
    def __init__(self, channels: Union[None, List[str]] = None, groups: Union[None, List[str]] = None) -> None:
        super().__init__()
        self.channels = channels
        self.groups = groups


class HeartbeatWaitInvocation(PNManageableInvocation):
    def __init__(self, time) -> None:
        self.wait_time = time
        super().__init__()


class HeartbeatCancelWaitInvocation(PNCancelInvocation):
    cancel_effect = HeartbeatWaitInvocation.__name__


class HeartbeatLeaveInvocation(PNManageableInvocation):
    def __init__(self, channels: Union[None, List[str]] = None, groups: Union[None, List[str]] = None,
                 suppress_leave: bool = False) -> None:
        super().__init__()
        self.channels = channels
        self.groups = groups
        self.suppress_leave = suppress_leave


class HeartbeatDelayedHeartbeatInvocation(PNManageableInvocation):
    def __init__(self,
                 channels: Union[None, List[str]] = None,
                 groups: Union[None, List[str]] = None,
                 attempts: Union[None, int] = None,
                 reason: Union[None, PubNubException] = None):
        super().__init__()
        self.channels = channels
        self.groups = groups
        self.attempts = attempts
        self.reason = reason


class HeartbeatCancelDelayedHeartbeatInvocation(PNCancelInvocation):
    cancel_effect = HeartbeatDelayedHeartbeatInvocation.__name__
