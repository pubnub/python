class PNGetSpacesResult(object):
    def __init__(self, result):
        """
        Representation of get spaces server response

        :param result: result of get spaces operation
        """
        self.data = result['data']
        self.status = result['status']
        self.total_count = result.get('totalCount', None)
        self.next = result.get('next', None)
        self.prev = result.get('prev', None)

    def __str__(self):
        return "Get spaces success with data: %s" % self.data


class PNCreateSpaceResult(object):
    def __init__(self, result):
        """
        Representation of create space server response

        :param result: result of create space operation
        """
        self.data = result['data']
        self.status = result['status']

    def __str__(self):
        return "Space created with data: %s" % self.data


class PNGetSpaceResult(object):
    def __init__(self, result):
        """
        Representation of get space server response

        :param result: result of get space operation
        """
        self.data = result['data']
        self.status = result['status']

    def __str__(self):
        return "Get space success with data: %s" % self.data


class PNUpdateSpaceResult(object):
    def __init__(self, result):
        """
        Representation of update space server response

        :param result: result of update space operation
        """
        self.data = result['data']
        self.status = result['status']

    def __str__(self):
        return "Update space success with data: %s" % self.data


class PNDeleteSpaceResult(object):
    def __init__(self, result):
        """
        Representation of delete space server response

        :param result: result of delete space operation
        """
        self.data = result['data']
        self.status = result['status']

    def __str__(self):
        return "Delete space success with data: %s" % self.data


class PNSpaceResult(object):
    def __init__(self, event, data):
        self.data = data
        self.event = event

    def __str__(self):
        return "Space %s event with data: %s" % (self.event, self.data)
