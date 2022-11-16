from pubnub.models.consumer.entities.result import PNEntityPageableResult


class PNMembershipsResult(PNEntityPageableResult):
    _description = "Set Memberships: %s"

    def __init__(self, result):
        super().__init__(result)
        self.status = result["status"]

    def rename_channel(result):
        result['space'] = result.pop('channel')
        return result

    def rename_uuid(result):
        result['user'] = result.pop('uuid')
        return result


class PNUserMembershipsResult(PNMembershipsResult):
    def __init__(self, result):
        super().__init__(result)
        self.data = [PNMembershipsResult.rename_channel(space) for space in result['data']]


class PNSpaceMembershipsResult(PNMembershipsResult):
    def __init__(self, result):
        super().__init__(result)
        self.data = [PNMembershipsResult.rename_uuid(user) for user in result['data']]
