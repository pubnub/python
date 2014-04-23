
import sys


from PubnubUnitTest import Suite
from Pubnub import Pubnub

pubnub = Pubnub("demo", "demo")

tests_count = 1 + 2
test_suite = Suite(pubnub, tests_count)

tests = []


def test_publish():
    name = "Publish Test"

    def success(r):
        test_suite.test(r[0] == 1, name)

    def fail(e):
        test_suite.test(False, msg, e)

    pubnub.publish({
                   'channel': 'hello',
                   'message': 'hi',
                   'callback': success,
                   'error': fail
                   })
tests.append(test_publish)


def test_subscribe_publish():
    channel = "hello"
    name = "Subscribe Publish Test"
    publish_msg = "This is Pubnub Python-Twisted"

    def connect():
        def success(r):
            test_suite.test(r[0] == 1, name, "publish success")

        def fail(e):
            test_suite.test(False, name, "Publish Failed", e)

        pubnub.publish({
                       'channel': channel,
                       'message': publish_msg,
                       'callback': success,
                       'error': fail
                       })

    def callback(r):
        test_suite.test(r == publish_msg, name, "message received")

    pubnub.subscribe({
                     'channel': channel,
                     'callback': callback,
                     'connect': connect
                     })
tests.append(test_subscribe_publish)


for t in tests:
    t()

pubnub.start()
