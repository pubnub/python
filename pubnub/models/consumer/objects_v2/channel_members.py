from abc import abstractmethod, ABCMeta

from pubnub.models.consumer.objects_v2.page import PNPageable
from pubnub.utils import deprecated


class PNUUID:
    __metaclass__ = ABCMeta

    def __init__(self, uuid):
        self._uuid = uuid

    @staticmethod
    @deprecated(alternative='PNUserMember class')
    def uuid(uuid):
        return JustUUID(uuid)

    @staticmethod
    @deprecated(alternative='PNUserMember class')
    def uuid_with_custom(uuid, custom):
        return UUIDWithCustom(uuid, custom)

    @abstractmethod
    def to_payload_dict(self):
        return None


class JustUUID(PNUUID):
    def to_payload_dict(self):
        return {
            "uuid": {
                "id": str(self._uuid)
            }
        }


class UUIDWithCustom(PNUUID):
    def __init__(self, uuid, custom):
        PNUUID.__init__(self, uuid)
        self._custom = custom

    def to_payload_dict(self):
        return {
            "uuid": {
                "id": str(self._uuid)
            },
            "custom": dict(self._custom)
        }


class PNUserMember(PNUUID):
    """
    PNUser represents a user object with associated attributes and methods to convert it to a payload dictionary.

    Attributes
    ----------
    _user_id : str
        The unique identifier for the user.
    _type : str
        The type of the user.
    _status : str
        The status of the user.
    _custom : any
        Custom attributes associated with the user.

     Methods
    -------
    __init__(user_id: str = None, type: str = None, status: str = None, custom: any = None)
        Initializes a new instance of PNUser with required user_id, and optional type, status, and custom attributes.
    to_payload_dict()
        Converts the PNUser instance to a dictionary payload suitable for transmission.
    """

    _user_id: str
    _type: str
    _status: str
    _custom: any

    @property
    def _uuuid(self):
        return self._user_id

    def __init__(self, user_id: str, type: str = None, status: str = None, custom: any = None):
        """
        Initialize a PNUser object. If optional values are omitted then they won't be included in the payload.

        Parameters
        ----------
        user_id : str
            The unique identifier for the user.
        type : str, optional
            The type of the channel member (default is None).
        status : str, optional
            The status of the channel member (default is None).
        custom : any, optional
            Custom data associated with the channel member (default is None).
        """

        self._user_id = user_id
        self._type = type
        self._status = status
        self._custom = custom

    def to_payload_dict(self):
        """
        Convert the objects attributes to a dictionary payload.

        Returns

        -------
        dict
            A dictionary containing the objects attributes:
            - "uuid": A dictionary with the member's UUID.
            - "type": The type of the member, if available.
            - "status": The status of the member, if available.
            - "custom": Custom attributes of the member, if available.
        """

        payload = {
            "uuid": {
                "id": str(self._user_id)
            },
        }
        if self._type:
            payload["type"] = str(self._type)
        if self._status:
            payload["status"] = str(self._status)
        if self._custom:
            payload["custom"] = dict(self._custom)
        return payload


class PNSetChannelMembersResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Set Channel Members metatdata: %s" % self.data


class PNGetChannelMembersResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Get Channel Members metatdata: %s" % self.data


class PNRemoveChannelMembersResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Remove Channel Members metatdata: %s" % self.data


class PNManageChannelMembersResult(PNPageable):
    def __init__(self, result):
        PNPageable.__init__(self, result)
        self.data = result["data"]
        self.status = result["status"]

    def __str__(self):
        return "Manage Channel Members metatdata: %s" % self.data
