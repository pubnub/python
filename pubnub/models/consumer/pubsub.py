class PNMessageResult(object):
    def __init__(self, message, subscribed_channel, actual_channel, timetoken, user_metadata=None):
        assert message is not None
        assert isinstance(subscribed_channel, (str, unicode))
        assert isinstance(actual_channel, (str, unicode))
        assert isinstance(timetoken, long)

        if user_metadata is not None:
            assert isinstance(user_metadata, object)

        self.message = message
        self.subscribed_channel = subscribed_channel
        self.actual_channel = actual_channel
        self.timetoken = timetoken
        self.user_metadata = user_metadata


class PNPresenceEventResult(object):
    def __init__(self, event, uuid, timestamp, occupancy, subscribed_channel, actual_channel,
                 timetoken, user_metadata=None):

        assert isinstance(event, str)
        assert isinstance(uuid, str)
        assert isinstance(timestamp, long)
        assert isinstance(occupancy, int)
        assert isinstance(actual_channel, str)
        assert isinstance(timetoken, long)

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
        Representation of server response

        :param envelope: original response from server
        :param timetoken: of publish operation
        """
        self.original_response = envelope
        self.envelope = envelope
        self.timetoken = timetoken
