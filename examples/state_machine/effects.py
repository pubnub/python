from typing import Union
from pubnub.exceptions import PubNubException


class PNEffect:
    pass


class HandshakeEffect(PNEffect):
    def __init__(self, channels: Union[None, list[str]], groups: Union[None, list[str]]) -> None:
        super().__init__()
        self.channels = channels
        self.groups = groups


class CancelHandshakeEffect(PNEffect):
    pass


class ReceiveMessagesEffect(PNEffect):
    def __init__(self,
                 channels: Union[None, list[str]],
                 groups: Union[None, list[str]],
                 timetoken: Union[None, str],
                 region: Union[None, str]
                 ) -> None:
        super().__init__()
        self.channels = channels
        self.groups = groups
        self.timetoken = timetoken
        self.region = region


class CancelReceiveMessagesEffect(PNEffect):
    pass


class EmitMessagesEffect(PNEffect):
    def __init__(self, messages: Union[None, list[str]]) -> None:
        super().__init__()
        self.messages = messages


class HandshakeReconnectEffect(PNEffect):
    def __init__(self,
                 channels: Union[None, list[str]],
                 groups: Union[None, list[str]],
                 attempts: Union[None, int],
                 reason: Union[None, PubNubException]
                 ) -> None:
        self.channels = channels
        self.groups = groups
        self.attempts = attempts
        self.reason = reason


class CancelHandshakeReconnectEffect(PNEffect):
    pass


class ReceiveReconnectEffect(PNEffect):
    def __init__(self,
                 channels: Union[None, list[str]],
                 groups: Union[None, list[str]],
                 timetoken: Union[None, str],
                 region: Union[None, str],
                 attempts: Union[None, int],
                 reason: Union[None, PubNubException]
                 ) -> None:
        self.channels = channels
        self.groups = groups
        self.timetoken = timetoken
        self.region = region
        self.attempts = attempts
        self.reason = reason
