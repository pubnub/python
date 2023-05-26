from typing import List, Union
from pubnub.exceptions import PubNubException
from pubnub.enums import PNStatusCategory
from pubnub.pubnub import PubNub


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


class HandshakeReconnectEffect(PNManageableEffect):
    def __init__(self,
                 channels: Union[None, List[str]] = None,
                 groups: Union[None, List[str]] = None,
                 attempts: Union[None, int] = None,
                 reason: Union[None, PubNubException] = None
                 ) -> None:
        self.channels = channels
        self.groups = groups
        self.attempts = attempts
        self.reason = reason


class CancelHandshakeReconnectEffect(PNCancelEffect):
    cancel_effect = HandshakeReconnectEffect.__name__


class ReceiveReconnectEffect(PNManageableEffect):
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
        self.timetoken = timetoken
        self.region = region
        self.attempts = attempts
        self.reason = reason


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


class ManagedEffect:
    pubnub: PubNub
    effect: Union[PNManageableEffect, PNCancelEffect]

    def set_pn(pubnub: PubNub):
        pubnub = pubnub

    def __init__(self, effect: Union[PNManageableEffect, PNCancelEffect]) -> None:
        self.effect = effect

    def run(self):
        pass

    def stop(self):
        pass


class EmitEffect:
    pubnub: PubNub

    def set_pn(pubnub: PubNub):
        pubnub = pubnub

    def emit(self, effect: PNEmittableEffect):
        if isinstance(effect, EmitMessagesEffect):
            self.emit_message(effect)
        if isinstance(effect, EmitStatusEffect):
            self.emit_status(effect)

    def emit_message(self, effect: EmitMessagesEffect):
        pass

    def emit_status(self, effect: EmitStatusEffect):
        pass
