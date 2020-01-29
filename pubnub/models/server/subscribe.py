import six


class SubscribeEnvelope:
    def __init__(self, messages=None, metadata=None):
        assert isinstance(messages, (list, None))
        assert isinstance(metadata, (SubscribeMetadata, None))

        self.messages = messages
        self.metadata = metadata

    @classmethod
    def from_json(cls, json_input):
        messages = []

        for raw_message in json_input['m']:
            messages.append(SubscribeMessage.from_json(raw_message))

        metadata = SubscribeMetadata.from_json(json_input['t'])
        return SubscribeEnvelope(messages, metadata)


class SubscribeMessage:
    def __init__(self):
        self.shard = None
        self.subscription_match = None
        self.channel = None
        self.payload = None
        self.flags = None
        self.issuing_client_id = None
        self.subscribe_key = None
        self.origination_timetoken = None
        self.publish_metadata = None
        self.only_channel_subscription = False
        self.type = 0

    @classmethod
    def from_json(cls, json_input):
        message = SubscribeMessage()
        if 'a' in json_input:
            message.shard = json_input['a']
        if 'b' in json_input:
            message.subscription_match = json_input['b']
        message.channel = json_input['c']
        message.payload = json_input['d']
        message.flags = json_input['f']
        if 'i' in json_input:
            message.issuing_client_id = json_input['i']
        message.subscribe_key = json_input['k']
        if 'o' in json_input:
            message.origination_timetoken = json_input['o']
        message.publish_metadata = PublishMetadata.from_json(json_input['p'])
        if 'e' in json_input:
            message.type = json_input['e']
        return message


class SubscribeMetadata:
    def __init__(self, timetoken=None, region=None):
        self.timetoken = timetoken
        self.region = region

    @classmethod
    def from_json(cls, json_input):
        assert isinstance(json_input, dict)
        assert 'r' in json_input
        assert 't' in json_input

        return SubscribeMetadata(json_input['t'], json_input['r'])


class PresenceEnvelope:
    def __init__(self, action, uuid, occupancy, timestamp, data=None):
        assert isinstance(action, six.string_types)
        assert isinstance(occupancy, six.integer_types)
        assert isinstance(timestamp, six.integer_types)
        if data is not None:
            assert isinstance(data, dict)

        self.action = action
        self.uuid = uuid
        self.occupancy = occupancy
        self.timestamp = timestamp
        self.data = data

    @classmethod
    def extract_value(cls, json, key):
        if key in json:
            return json[key]
        else:
            return None

    @classmethod
    def from_json_payload(cls, json):

        return PresenceEnvelope(
            action=cls.extract_value(json, 'action'),
            uuid=cls.extract_value(json, 'uuid'),
            occupancy=cls.extract_value(json, 'occupancy'),
            timestamp=cls.extract_value(json, 'timestamp'),
            data=cls.extract_value(json, 'data')
        )


class PublishMetadata:
    def __init__(self, publish_timetoken=None, region=None):
        self.publish_timetoken = publish_timetoken
        self.region = region

    @classmethod
    def from_json(cls, json_input):
        assert 'r' in json_input
        assert 't' in json_input

        return PublishMetadata(int(json_input['t']), int(json_input['r']))
