# PubNub HereNow usage example
import sys

sys.path.append("../../")

from examples import pnconf
from pubnub.pubnub_twisted import PubNubTwisted


pubnub = PubNubTwisted(pnconf)


def successHandler(env):
    print("success >>>")
    print(env.result.timetoken)
    pubnub.stop()


def errorHandler(err):
    print("error >>>")
    print(err)
    pubnub.stop()


def async_callback(result, status):
    if status.is_error():
        print("async error >>>")
        print(status.error_data.information)
    else:
        print("async result >>>")
        print(result.timetoken)


# using deferred:
deferred = pubnub.publish() \
    .channel("my_channel") \
    .message("hey")\
    .deferred()

deferred.addCallback(successHandler)
deferred.addErrback(errorHandler)

# using deferred:
deferred = pubnub.publish() \
    .channel("my_channel") \
    .message("hey")\
    .deferred()

deferred.addCallback(successHandler)
deferred.addErrback(errorHandler)

# using async:
pubnub.publish() \
    .channel("my_channel") \
    .message("hey")\
    .async(async_callback)

pubnub.start()
