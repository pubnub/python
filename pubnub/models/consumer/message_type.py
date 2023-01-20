class PNMessageType:
    _internal_type: str = 0
    _user_type: str = None

    def __init__(self, user_type: str = None) -> None:
        self._user_type = user_type

    def set_internal_type(self, internal_type: str):
        self._internal_type = internal_type

    def from_response(user_type: str = None, internal_type: str = None):
        message_type = PNMessageType(user_type)
        if internal_type is not None:
            message_type.set_internal_type(internal_type)
        return message_type

    def __str__(self) -> str:
        return self._user_type if self._user_type is not None else str(self._internal_type)

    def toJSON(self) -> str:
        return str(self)
