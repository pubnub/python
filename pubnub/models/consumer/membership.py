class PNGetSpaceMembershipsResult(object):
    def __init__(self, result):
        """
        Representation of get space memberships server response

        :param result: result of get space memberships operation
        """
        self.data = result['data']
        self.status = result['status']
        self.total_count = result.get('totalCount', None)
        self.next = result.get('next', None)
        self.prev = result.get('prev', None)

    def __str__(self):
        return "Get space memberships success with data: %s" % self.space


class PNUpdateSpaceMembershipsResult(object):
    def __init__(self, result):
        """
        Representation of update space memeberships response

        :param result: result of update space memeberships operation
        """
        self.data = result['data']
        self.status = result['status']
        self.total_count = result.get('totalCount', None)
        self.next = result.get('next', None)
        self.prev = result.get('prev', None)

    def __str__(self):
        return "Update space memebership success with data: %s" % self.data


class PNGetMembersResult(object):
    def __init__(self, result):
        """
        Representation of fetch user server response

        :param result: result of fetch user operation
        """
        self.data = result['data']
        self.status = result['status']
        self.total_count = result.get('totalCount', None)
        self.next = result.get('next', None)
        self.prev = result.get('prev', None)

    def __str__(self):
        return "Get members success with data: %s" % self.data


class PNUpdateMembersResult(object):
    def __init__(self, result):
        """
        Representation of update members server response

        :param result: result of update members operation
        """
        self.data = result['data']
        self.status = result['status']
        self.total_count = result.get('totalCount', None)
        self.next = result.get('next', None)
        self.prev = result.get('prev', None)

    def __str__(self):
        return "Update update members success with data: %s" % self.data
