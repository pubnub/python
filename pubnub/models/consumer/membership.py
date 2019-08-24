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


class PNManageMembershipsResult(object):
    def __init__(self, result):
        """
        Representation of manage memeberships response

        :param result: result of manage memeberships operation
        """
        self.data = result['data']
        self.status = result['status']
        self.total_count = result.get('totalCount', None)
        self.next = result.get('next', None)
        self.prev = result.get('prev', None)

    def __str__(self):
        return "Manage memeberships success with data: %s" % self.data


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


class PNManageMembersResult(object):
    def __init__(self, result):
        """
        Representation of manage members server response

        :param result: result of manage members operation
        """
        self.data = result['data']
        self.status = result['status']
        self.total_count = result.get('totalCount', None)
        self.next = result.get('next', None)
        self.prev = result.get('prev', None)

    def __str__(self):
        return "Manage members success with data: %s" % self.data


class PNMembershipResult(object):
    def __init__(self, event, data):
        self.data = data
        self.event = event

    def __str__(self):
        return "Membership %s event with data: %s" % (self.event, self.data)
