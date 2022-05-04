from abc import ABCMeta


class PNPage:
    __metaclass__ = ABCMeta

    def __init__(self, hash):
        self._hash = str(hash)

    @property
    def hash(self):
        return self._hash

    @classmethod
    def builder(cls, value):
        if value is None:
            return None
        return cls(value)


class Next(PNPage):
    def __init__(self, hash):
        super().__init__(hash)


class Previous(PNPage):
    def __init__(self, hash):
        super().__init__(hash)


class PNPageable(object):
    __metaclass__ = ABCMeta

    def __init__(self, result):
        self.total_count = result.get('totalCount', None)
        self.next = Next.builder(result.get("next", None))
        self.prev = Previous.builder(result.get("prev", None))
