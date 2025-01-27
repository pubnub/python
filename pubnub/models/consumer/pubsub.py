from pubnub.models.consumer.message_actions import PNMessageAction


class PNMessageResult(object):
    def __init__(self, message, subscription, channel, timetoken, user_metadata=None, publisher=None,
                 error=None, custom_message_type=None):

        if subscription is not None:
            assert isinstance(subscription, str)

        if channel is not None:
            assert isinstance(channel, str)

        if publisher is not None:
            assert isinstance(publisher, str)

        assert isinstance(timetoken, int)

        if user_metadata is not None:
            assert isinstance(user_metadata, object)

        self.message = message
        # DEPRECATED: subscribed_channel and actual_channel properties are deprecated
        # self.subscribed_channel = subscribed_channel <= now known as subscription
        # self.actual_channel = actual_channel <= now known as channel

        self.channel = channel
        self.subscription = subscription

        self.timetoken = timetoken
        self.user_metadata = user_metadata
        self.publisher = publisher
        self.error = error
        self.custom_message_type = custom_message_type


class PNSignalMessageResult(PNMessageResult):
    pass


class PNFileMessageResult(PNMessageResult):
    def __init__(
            self, message, subscription,
            channel, timetoken, publisher,
            file_url, file_id, file_name, user_metadata=None, custom_message_type=None
    ):
        super(PNFileMessageResult, self).__init__(message, subscription, channel, timetoken, user_metadata, publisher,
                                                  custom_message_type=custom_message_type)
        self.file_url = file_url
        self.file_id = file_id
        self.file_name = file_name


class PNPresenceEventResult(object):
    def __init__(self, event, uuid, timestamp, occupancy, subscription, channel,
                 timetoken, state, join, leave, timeout, user_metadata=None):

        assert isinstance(event, str)
        assert isinstance(timestamp, int)
        assert isinstance(occupancy, int)
        assert isinstance(channel, str)
        assert isinstance(timetoken, int)

        if user_metadata is not None:
            assert isinstance(user_metadata, object)

        if state is not None:
            assert isinstance(state, dict)

        self.event = event
        self.uuid = uuid
        self.timestamp = timestamp
        self.occupancy = occupancy
        self.state = state
        self.join = join
        self.leave = leave
        self.timeout = timeout

        # DEPRECATED: subscribed_channel and actual_channel properties are deprecated
        # self.subscribed_channel = subscribed_channel <= now known as subscription
        # self.actual_channel = actual_channel <= now known as channel
        self.subscription = subscription
        self.channel = channel

        self.timetoken = timetoken
        self.user_metadata = user_metadata


class PNMessageActionResult(PNMessageAction):
    def __init__(self, result, *, subscription=None, channel=None):
        super(PNMessageActionResult, self).__init__(result)
        self.subscription = subscription
        self.channel = channel


class PNPublishResult(object):
    def __init__(self, envelope, timetoken):
        """
        Representation of publish server response

        :param timetoken: of publish operation
        """
        self.timetoken = timetoken

    def __str__(self):
        return "Publish success with timetoken %s" % self.timetoken


class PNFireResult(object):
    def __init__(self, envelope, timetoken):
        """
        Representation of fire server response

        :param timetoken: of fire operation
        """
        self.timetoken = timetoken

    def __str__(self):
        return "Fire success with timetoken %s" % self.timetoken
