from abc import ABCMeta


class PNPage:
    __metaclass__ = ABCMeta

    def __init__(self, hash):
        self._hash = str(hash)

    @property
    def hash(self):
        return self._hash


class Next(PNPage):
    def __init__(self, hash):
        PNPage.__init__(self, hash)


class Previous(PNPage):
    def __init__(self, hash):
        PNPage.__init__(self, hash)


class PNPageable(object):
    __metaclass__ = ABCMeta

    def __init__(self, result):
        self.total_count = result.get('totalCount', None)
        if result.get("next", None):
            self.next = Next(result["next"])
        else:
            self.next = None

        if result.get("prev", None):
            self.prev = Previous(result["prev"])
        else:
            self.prev = None
