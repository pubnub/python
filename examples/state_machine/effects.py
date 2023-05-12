from typing import Union


class PNEffect:
    pass


class HandshakeEffect(PNEffect):
    def __init__(self, channels: Union[None, list[str]], groups: Union[None, list[str]]) -> None:
        super().__init__()
        self.channels = channels
        self.groups = groups


class CancelHandshakeEffect(PNEffect):
    pass


class ReceiveEventsEffect(PNEffect):
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


class CancelReceiveEventsEffect(PNEffect):
    pass

class EmitEventsEffect(PNEffect):
    def __init__(self, events: Union[None, list[str]]) -> None:
        super().__init__()
        self.events = events


class ReconnectEffect(PNEffect):
    def __init__(self, context: dict) -> None:
        super().__init__()
        self.context = context


class HandshakeReconnectEffect(PNEffect):
    def __init__(self, context: dict) -> None:
        super().__init__()
        self.context = context
