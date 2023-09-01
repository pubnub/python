from typing import List, Union
from pubnub.exceptions import PubNubException
from pubnub.enums import PNStatusCategory


class PNEffect:
    pass


class PNManageableEffect(PNEffect):
    pass


class PNCancelEffect(PNEffect):
    cancel_effect: str


class HandshakeEffect(PNManageableEffect):
    def __init__(self, channels: Union[None, List[str]] = None, groups: Union[None, List[str]] = None) -> None:
        super().__init__()
        self.channels = channels
        self.groups = groups


class CancelHandshakeEffect(PNCancelEffect):
    cancel_effect = HandshakeEffect.__name__


class ReceiveMessagesEffect(PNManageableEffect):
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


class CancelReceiveMessagesEffect(PNCancelEffect):
    cancel_effect = ReceiveMessagesEffect.__name__


class ReconnectEffect(PNManageableEffect):
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


class HandshakeReconnectEffect(ReconnectEffect):
    pass


class CancelHandshakeReconnectEffect(PNCancelEffect):
    cancel_effect = HandshakeReconnectEffect.__name__


class ReceiveReconnectEffect(ReconnectEffect):
    pass


class CancelReceiveReconnectEffect(PNCancelEffect):
    cancel_effect = ReceiveReconnectEffect.__name__


class PNEmittableEffect(PNEffect):
    pass


class EmitMessagesEffect(PNEmittableEffect):
    def __init__(self, messages: Union[None, List[str]]) -> None:
        super().__init__()
        self.messages = messages


class EmitStatusEffect(PNEmittableEffect):
    def __init__(self, status: Union[None, PNStatusCategory]) -> None:
        super().__init__()
        self.status = status
