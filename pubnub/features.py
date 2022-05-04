from pubnub.exceptions import PubNubException


def feature_flag(flag):
    def inner(method):
        if not flag:
            raise PubNubException(errormsg='This feature is not enabled')
        return method
    return inner


pn_enable_entities = True
