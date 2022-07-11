from os import getenv
from pubnub.exceptions import PubNubException

flags = {
    'PN_ENABLE_ENTITIES': getenv('PN_ENABLE_ENTITIES', False)
}


def feature_flag(flag):
    def not_implemented(*args, **kwargs):
        raise PubNubException(errormsg='This feature is not enabled')

    def inner(method):
        if flag not in flags.keys():
            raise PubNubException(errormsg='Flag not supported')

        if not flags[flag]:
            return not_implemented
        return method
    return inner
