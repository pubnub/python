"""
Possible responses of PAM request
"""


class _PAMResult:
    def __init__(self, level, subscribe_key, channels, groups, uuids, ttl=None, r=None, w=None, m=None, d=None):
        self.level = level
        self.subscribe_key = subscribe_key
        self.channels = channels
        self.groups = groups
        self.uuids = uuids
        self.ttl = ttl
        self.read_enabled = r
        self.write_enabled = w
        self.manage_enabled = m
        self.delete_enabled = d

    @classmethod
    def from_json(cls, json_input):
        constructed_channels = {}
        constructed_groups = {}
        constructed_uuids = {}

        # only extract ttl, others are to be fetched on per uuid level
        r, w, m, d, g, u, j, ttl = fetch_permissions(json_input)

        if 'channel' in json_input:
            channel_name = json_input['channel']
            constructed_auth_keys = {}
            for auth_key_name, value in json_input['auths'].items():
                constructed_auth_keys[auth_key_name] = PNAccessManagerKeyData.from_json(value)

            constructed_channels[channel_name] = PNAccessManagerChannelData(
                name=channel_name,
                auth_keys=constructed_auth_keys,
                ttl=ttl
            )

        if 'channel-group' in json_input:
            if isinstance(json_input['channel-group'], str):
                group_name = json_input['channel-group']
                constructed_auth_keys = {}
                for auth_key_name, value in json_input['auths'].items():
                    constructed_auth_keys[auth_key_name] = PNAccessManagerKeyData.from_json(value)
                constructed_groups[group_name] = PNAccessManagerChannelGroupData(
                    name=group_name,
                    auth_keys=constructed_auth_keys,
                    ttl=ttl
                )

        if 'channel-groups' in json_input:
            if isinstance(json_input['channel-groups'], str):
                group_name = json_input['channel-groups']
                constructed_auth_keys = {}
                for auth_key_name, value in json_input['auths'].items():
                    constructed_auth_keys[auth_key_name] = PNAccessManagerKeyData.from_json(value)
                constructed_groups[group_name] = PNAccessManagerChannelGroupData(
                    name=group_name,
                    auth_keys=constructed_auth_keys,
                    ttl=ttl
                )
            if isinstance(json_input['channel-groups'], dict):
                for group_name, value in json_input['channel-groups'].items():
                    constructed_groups[group_name] = PNAccessManagerChannelGroupData.from_json(group_name, value)

        if 'channels' in json_input:
            for channel_name, value in json_input['channels'].items():
                constructed_channels[channel_name] = PNAccessManagerChannelData.from_json(channel_name, value)

        if 'uuids' in json_input:
            for uuid, value in json_input['uuids'].items():
                constructed_uuids[uuid] = PNAccessManagerUuidsData.from_json(uuid, value)

        return cls(
            level=json_input['level'],
            subscribe_key=json_input['subscribe_key'],
            channels=constructed_channels,
            groups=constructed_groups,
            uuids=constructed_uuids,
            r=r,
            w=w,
            m=m,
            d=d,
            ttl=ttl,
        )


class PNAccessManagerResult(_PAMResult):
    def __str__(self):
        return "Permissions are valid for %d minutes" % self.ttl or 0


class PNAccessManagerAuditResult(PNAccessManagerResult):
    pass


class PNAccessManagerGrantResult(PNAccessManagerResult):
    pass


class _PAMEntityData(object):
    def __init__(self, name, auth_keys=None, r=None, w=None, m=None, d=None, g=None, u=None, j=None, ttl=None):
        self.name = name
        self.auth_keys = auth_keys
        self.read_enabled = r
        self.write_enabled = w
        self.manage_enabled = m
        self.delete_enabled = d
        self.get = g
        self.update = u
        self.join = j
        self.ttl = ttl

    @classmethod
    def from_json(cls, name, json_input):
        r, w, m, d, g, u, j, ttl = fetch_permissions(json_input)
        constructed_auth_keys = {}

        if 'auths' in json_input:
            for auth_key, value in json_input['auths'].items():
                constructed_auth_keys[auth_key] = PNAccessManagerKeyData.from_json(value)

        return cls(name, constructed_auth_keys, r, w, m, d, g, u, j, ttl)


class PNAccessManagerChannelData(_PAMEntityData):
    pass


class PNAccessManagerChannelGroupData(_PAMEntityData):
    pass


class PNAccessManagerUuidsData(_PAMEntityData):
    pass


class PNAccessManagerKeyData(object):
    def __init__(self, r, w, m, d, g, u, j, ttl=None):
        self.read_enabled = r
        self.write_enabled = w
        self.manage_enabled = m
        self.delete_enabled = d
        self.get = g
        self.update = u
        self.join = j
        self.ttl = ttl

    @classmethod
    def from_json(cls, json_input):
        r, w, m, d, g, u, j, ttl = fetch_permissions(json_input)
        return PNAccessManagerKeyData(r, w, m, d, g, u, j, ttl)


def fetch_permissions(json_input):
    r = None
    w = None
    m = None
    d = None
    g = None
    u = None
    j = None
    ttl = None

    if 'r' in json_input:
        r = json_input['r'] == 1

    if 'w' in json_input:
        w = json_input['w'] == 1

    if 'm' in json_input:
        m = json_input['m'] == 1

    if 'd' in json_input:
        d = json_input['d'] == 1

    if 'g' in json_input:
        g = json_input['g'] == 1

    if 'u' in json_input:
        u = json_input['u'] == 1

    if 'j' in json_input:
        j = json_input['j'] == 1

    if 'ttl' in json_input:
        ttl = json_input['ttl']

    return r, w, m, d, g, u, j, ttl
