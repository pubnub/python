class PNGetUsersResult(object):
    def __init__(self, result):
        """
        Representation of get users server response

        :param result: result of get users operation
        """
        self.data = result['data']
        self.status = result['status']

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
