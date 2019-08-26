class PNGetUsersResult(object):
    def __init__(self, result):
        """
        Representation of get users server response

        :param result: result of get users operation
        """
        self.data = result['data']
        self.status = result['status']
        self.total_count = result.get('totalCount', None)
        self.next = result.get('next', None)
        self.prev = result.get('prev', None)

    def __str__(self):
        return "Get users success with data: %s" % self.data


class PNCreateUserResult(object):
    def __init__(self, result):
        """
        Representation of create user server response

        :param result: result of create user operation
        """
        self.data = result['data']
        self.status = result['status']

    def __str__(self):
        return "User created with data: %s" % self.data


class PNGetUserResult(object):
    def __init__(self, result):
        """
        Representation of get user server response

        :param result: result of get user operation
        """
        self.data = result['data']
        self.status = result['status']

    def __str__(self):
        return "Get user success with data: %s" % self.data


class PNUpdateUserResult(object):
    def __init__(self, result):
        """
        Representation of update user server response

        :param result: result of update user operation
        """
        self.data = result['data']
        self.status = result['status']

    def __str__(self):
        return "Update user success with data: %s" % self.data


class PNDeleteUserResult(object):
    def __init__(self, result):
        """
        Representation of delete user server response

        :param result: result of delete user operation
        """
        self.data = result['data']
        self.status = result['status']

    def __str__(self):
        return "Delete user success with data: %s" % self.data


class PNUserResult(object):
    def __init__(self, event, data):
        self.data = data
        self.event = event

    def __str__(self):
        return "User %s event with data: %s" % (self.event, self.data)
