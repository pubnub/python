class SubscriptionItem(object):
    def __init__(self, name=None, state=None):
        self.name = name
        self.state = state

    def __str__(self):
        return self.name
