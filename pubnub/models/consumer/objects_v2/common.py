class PNIncludes:
    field_mapping = {
        'custom': 'custom',
        'status': 'status',
        'type': 'type',
        'total_count': 'totalCount',
        'channel': 'channel',
        'channel_id': 'channel.id',
        'channel_custom': 'channel.custom',
        'channel_type': 'channel.type',
        'channel_status': 'channel.status',
        'user': 'uuid',
        'user_id': 'uuid.id',
        'user_custom': 'uuid.custom',
        'user_type': 'uuid.type',
        'user_status': 'uuid.status',
    }

    def __str__(self):
        return ','.join([self.field_mapping[k] for k, v in self.__dict__.items() if v])


class MembershipIncludes(PNIncludes):
    def __init__(self, custom: bool = False, status: bool = False, type: bool = False,
                 total_count: bool = False, channel: bool = False, channel_custom: bool = False,
                 channel_type: bool = False, channel_status: bool = False):
        self.custom = custom
        self.status = status
        self.type = type
        self.total_count = total_count
        self.channel = channel
        self.channel_custom = channel_custom
        self.channel_type = channel_type
        self.channel_status = channel_status


class MemberIncludes(PNIncludes):
    def __init__(self, custom: bool = False, status: bool = False, type: bool = False,
                 total_count: bool = False, user: bool = False, user_custom: bool = False,
                 user_type: bool = False, user_status: bool = False):
        self.custom = custom
        self.status = status
        self.type = type
        self.total_count = total_count
        self.user = user
        self.user_custom = user_custom
        self.user_type = user_type
        self.user_status = user_status
