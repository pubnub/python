class PNPublishResult(object):
    def __init__(self, original_response, timetoken):
        self.original_response = original_response
        self.timetoken = timetoken
