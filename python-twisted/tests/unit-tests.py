
import sys
import time


from PubnubUnitTest import Suite
from Pubnub import Pubnub

pubnub = Pubnub("demo", "demo")

tests_count = 1 + 2 + 1
test_suite = Suite(pubnub, tests_count)

tests = []


def test_publish():
    channel = "hello" + str(time.time())
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

#"""


def test_subscribe_publish():
    channel = "hello" + str(time.time())
    name = "Subscribe Publish Test"
    publish_msg = "This is Pubnub Python-Twisted"

    def connect():
        #print 'connect'
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
#"""


def test_here_now():
    channel = "hello12"  # + str(time.time())
    name = "Here Now Test"

    def connect():
        print 'connect'

        def call_here_now():
            print 'call_here_now'

            def success(r):
                test_suite.test(r['occupancy'] == 1, name, "Here Now success")

            def fail(e):
                test_suite.test(False, name, "Here Now Failed", e)

            pubnub.here_now({
                            'channel': channel,
                            'callback': success,
                            'error': fail
                            })
        pubnub.timeout(5, call_here_now)

    def callback(r):
        pass
    print 'Subscribe'
    pubnub.subscribe({
                     'channel': channel,
                     'callback': callback,
                     'connect': connect
                     })
tests.append(test_here_now)


for t in tests:
    t()

pubnub.start()
