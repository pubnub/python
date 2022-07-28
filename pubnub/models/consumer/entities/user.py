from typing import Optional

from pubnub.models.consumer.entities.result import PNEntityPageableResult, PNEntityResult


class PNCreateUserResult(PNEntityResult):
    _description = "Create User: %s"


class PNUpdateUserResult(PNEntityResult):
    _description = "Update User: %s"


class PNFetchUserResult(PNEntityResult):
    _description = "Fetch User: %s"


class PNRemoveUserResult(PNEntityResult):
    _description = "Remove User: %s"


class PNFetchUsersResult(PNEntityPageableResult):
    _description = "Fetch Users: %s"


class PNUserResult(PNEntityResult):
    def __str__(self):
        return "UUID %s event with data: %s" % (self.event, self.data)


class User:
    user_id: str
    custom: Optional[dict]

    def __init__(self, user_id=None, **kwargs):
        self.user_id = user_id
        if 'custom' in kwargs.keys():
            self.custom = kwargs['custom']

    def to_payload_dict(self):
        result = {
            "uuid": {
                "id": str(self.user_id)
            }
        }
        if 'custom' in self.__dict__.keys():
            result['custom'] = self.custom
        return result
