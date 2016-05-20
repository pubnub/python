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
