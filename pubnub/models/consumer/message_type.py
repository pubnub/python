class PNMessageType:
    _internal_type: str = None
    _user_type: str = None
    _type_mapping = {
        'None': 'message',
        '0': 'message',
        '1': 'signal',
        '2': 'object',
        '3': 'message_action',
        '4': 'file',
    }

    def __init__(self, user_type: str = None) -> None:
        self._user_type = user_type

    def set_internal_type(self, internal_type: str):
        self._internal_type = self._type_mapping[str(internal_type)]
        return self

    def from_response(user_type: str = None, internal_type: str = None):
        return PNMessageType(user_type).set_internal_type(internal_type)

    def __str__(self) -> str:
        return self._user_type if self._user_type is not None else str(self._internal_type)

    def toJSON(self) -> str:
        return str(self)
