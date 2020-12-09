from enum import Enum


class PNSortKeyValue(Enum):
    ID = 1
    NAME = 2
    UPDATED = 3


class PNSortDirection(Enum):
    ASC = 1
    DESC = 2


class PNSortKey:
    def __init__(self, sort_key_value, direction):
        self._sort_key_value = sort_key_value
        self._direction = direction

    @staticmethod
    def asc(sort_key_value):
        return PNSortKey(sort_key_value, PNSortDirection.ASC)

    @staticmethod
    def desc(sort_key_value):
        return PNSortKey(sort_key_value, PNSortDirection.DESC)

    def key_str(self):
        if self._sort_key_value == PNSortKeyValue.ID:
            return "id"
        elif self._sort_key_value == PNSortKeyValue.NAME:
            return "name"
        elif self._sort_key_value == PNSortKeyValue.UPDATED:
            return "updated"
        else:
            raise ValueError()

    def dir_str(self):
        if self._direction == PNSortDirection.ASC:
            return "asc"
        elif self._direction == PNSortDirection.DESC:
            return "desc"
        else:
            raise ValueError()
