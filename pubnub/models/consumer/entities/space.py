from typing import Optional
from pubnub.models.consumer.entities.result import PNEntityPageableResult, PNEntityResult


class PNCreateSpaceResult(PNEntityResult):
    _description = "Create Space: %s"


class PNUpdateSpaceResult(PNEntityResult):
    _description = "Update Space: %s"


class PNFetchSpaceResult(PNEntityResult):
    _description = "Fetch Space: %s"


class PNRemoveSpaceResult(PNEntityResult):
    _description = "Remove Space: %s"


class PNFetchSpacesResult(PNEntityPageableResult):
    _description = "Fetch Spaces: %s"


class PNSpaceResult(PNEntityResult):
    def __str__(self):
        return "Space %s event with data: %s" % (self.event, self.data)


class Space:
    space_id: str
    custom: Optional[dict]

    def __init__(self, space_id=None, **kwargs):
        self.space_id = space_id
        if 'custom' in kwargs.keys():
            self.custom = kwargs['custom']

    def to_payload_dict(self):
        result = {
            "channel": {
                "id": str(self.space_id)
            }
        }
        if 'custom' in self.__dict__.keys():
            result['custom'] = self.custom
        return result
