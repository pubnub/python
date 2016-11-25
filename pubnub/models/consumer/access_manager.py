import six
"""
Possible responses of PAM request
"""


class _PAMResult(object):
    def __init__(self, level, subscribe_key, channels, groups, ttl=None, r=None, w=None, m=None):
        self.level = level
        self.subscribe_key = subscribe_key
        self.channels = channels
        self.groups = groups
        self.ttl = ttl
        self.read_enabled = r
        self.write_enabled = w
        self.manage_enabled = m

    @classmethod
    def from_json(cls, json_input):
        constructed_channels = {}
        constructed_groups = {}
        r, w, m, ttl = fetch_permissions(json_input)

        if 'channel' in json_input:
            channel_name = json_input['channel']
            constructed_auth_keys = {}
            for auth_key_name, value in six.iteritems(json_input['auths']):
                constructed_auth_keys[auth_key_name] = PNAccessManagerKeyData.from_json(value)

            constructed_channels[channel_name] = PNAccessManagerChannelData(
                name=channel_name,
                auth_keys=constructed_auth_keys,
                ttl=ttl
            )

        if 'channel-group' in json_input:
            if isinstance(json_input['channel-group'], six.string_types):
                group_name = json_input['channel-group']
                constructed_auth_keys = {}
                for auth_key_name, value in six.iteritems(json_input['auths']):
                    constructed_auth_keys[auth_key_name] = PNAccessManagerKeyData.from_json(value)
                constructed_groups[group_name] = PNAccessManagerChannelGroupData(
                    name=group_name,
                    auth_keys=constructed_auth_keys,
                    ttl=ttl
                )

        if 'channel-groups' in json_input:
            if isinstance(json_input['channel-groups'], six.string_types):
                group_name = json_input['channel-groups']
                constructed_auth_keys = {}
                for auth_key_name, value in six.iteritems(json_input['auths']):
                    constructed_auth_keys[auth_key_name] = PNAccessManagerKeyData.from_json(value)
                constructed_groups[group_name] = PNAccessManagerChannelGroupData(
                    name=group_name,
                    auth_keys=constructed_auth_keys,
                    ttl=ttl
                )
            if isinstance(json_input['channel-groups'], dict):
                for group_name, value in six.iteritems(json_input['channel-groups']):
                    constructed_groups[group_name] = \
                        PNAccessManagerChannelGroupData.from_json(group_name, value)

        if 'channels' in json_input:
            for channel_name, value in six.iteritems(json_input['channels']):
                constructed_channels[channel_name] = \
                    PNAccessManagerChannelData.from_json(channel_name, value)

        return cls(
            level=json_input['level'],
            subscribe_key=json_input['subscribe_key'],
            channels=constructed_channels,
            groups=constructed_groups,
            r=r,
            w=w,
            m=m,
            ttl=ttl,
        )


class PNAccessManagerAuditResult(_PAMResult):
    def __str__(self):
        return "Current permissions are valid for %d minutes: read %s, write %s, manage: %s" % \
               (self.ttl or 0, self.read_enabled, self.write_enabled, self.manage_enabled)


class PNAccessManagerGrantResult(_PAMResult):
    def __str__(self):
        return "New permissions are set for %d minutes: read %s, write %s, manage: %s" % \
               (self.ttl or 0, self.read_enabled, self.write_enabled, self.manage_enabled)


class _PAMEntityData(object):
    def __init__(self, name, auth_keys=None, r=None, w=None, m=None, ttl=None):
        self.name = name
        self.auth_keys = auth_keys
        self.read_enabled = r
        self.write_enabled = w
        self.manage_enabled = m
        self.ttl = ttl

    @classmethod
    def from_json(cls, name, json_input):
        r, w, m, ttl = fetch_permissions(json_input)
        constructed_auth_keys = {}

        if 'auths' in json_input:
            for auth_key, value in json_input['auths'].items():
                constructed_auth_keys[auth_key] = PNAccessManagerKeyData.from_json(value)

        return cls(name, constructed_auth_keys, r, w, m)


class PNAccessManagerChannelData(_PAMEntityData):
    pass


class PNAccessManagerChannelGroupData(_PAMEntityData):
    pass


class PNAccessManagerKeyData(object):
    def __init__(self, r, w, m, ttl=None):
        self.read_enabled = r
        self.write_enabled = w
        self.manage_enabled = m
        self.ttl = ttl

    @classmethod
    def from_json(cls, json_input):
        r, w, m, ttl = fetch_permissions(json_input)
        return PNAccessManagerKeyData(r, w, m, ttl)


def fetch_permissions(json_input):
    r = None
    w = None
    m = None
    ttl = None

    if 'r' in json_input:
        r = json_input['r'] == 1

    if 'w' in json_input:
        w = json_input['w'] == 1

    if 'm' in json_input:
        m = json_input['m'] == 1

    if 'ttl' in json_input:
        ttl = json_input['ttl']

    return r, w, m, ttl
