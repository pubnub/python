class PNGetUsersResult(object):
    def __init__(self, result):
        """
        Representation of get users server response

        :param result: result of signal operation
        """
        self.data = result['data']
        self.status = result['status']

    def __str__(self):
        return "Get users success with data: %s" % self.data
