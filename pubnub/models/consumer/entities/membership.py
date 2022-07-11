from pubnub.models.consumer.entities.result import PNEntityPageableResult


class PNMembershipsResult(PNEntityPageableResult):
    _description = "Set Memberships: %s"

    def __init__(self, result):
        self.data = [PNMembershipsResult.rename_channel(space) for space in result['data']]

        self.status = result["status"]

    def rename_channel(result):
        result['space'] = result.pop('channel')
        return result
