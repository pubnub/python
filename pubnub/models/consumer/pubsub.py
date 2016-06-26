import six


class PNMessageResult(object):
    def __init__(self, message, subscribed_channel, actual_channel, timetoken, user_metadata=None):
        assert message is not None
        assert isinstance(subscribed_channel, six.string_types)
        if actual_channel is not None:
            assert isinstance(actual_channel, six.string_types)
        assert isinstance(timetoken, six.integer_types)

        if user_metadata is not None:
            assert isinstance(user_metadata, object)

        self.message = message
        # RENAME: Confusing name (can be channel, wildcard channel or group)
        self.subscribed_channel = subscribed_channel
        self.actual_channel = actual_channel
        self.timetoken = timetoken
        self.user_metadata = user_metadata


class PNPresenceEventResult(object):
    def __init__(self, event, uuid, timestamp, occupancy, subscribed_channel, actual_channel,
                 timetoken, user_metadata=None):

        assert isinstance(event, six.string_types)
        assert isinstance(uuid, six.string_types)
        assert isinstance(timestamp, six.integer_types)
        assert isinstance(occupancy, six.integer_types)
        assert isinstance(actual_channel, six.string_types)
        assert isinstance(timetoken, six.integer_types)

        if user_metadata is not None:
            assert isinstance(user_metadata, object)

        self.event = event
        self.uuid = uuid
        self.timestamp = timestamp
        self.occupancy = occupancy
        self.subscribed_channel = subscribed_channel
        self.actual_channel = actual_channel
        self.timetoken = timetoken
        self.user_metadata = user_metadata


class PNPublishResult(object):
    def __init__(self, envelope, timetoken):
        """
        Representation of publish server response

        :param timetoken: of publish operation
        """
        self.timetoken = timetoken
