# www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

# PubNub Real-time Push APIs and Notifications Framework
# Copyright (c) 2010 Stephen Blum
# http://www.pubnub.com/

import datetime
import sys

from pubnub import PubnubTwisted as Pubnub

publish_key = len(sys.argv) > 1 and sys.argv[1] or 'demo'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'demo'
secret_key = len(sys.argv) > 3 and sys.argv[3] or 'demo'
cipher_key = len(sys.argv) > 4 and sys.argv[4] or 'demo'
ssl_on = len(sys.argv) > 5 and bool(sys.argv[5]) or False
origin = len(sys.argv) > 6 and sys.argv[6] or 'pubsub.pubnub.com'

# -----------------------------------------------------------------------
# Initiat Class
# -----------------------------------------------------------------------
pubnub = Pubnub(
    publish_key,
    subscribe_key,
    secret_key=secret_key,
    cipher_key=cipher_key,
    ssl_on=ssl_on,
    origin=origin
)
crazy = ' ~`!@#$%^&*( 顶顅 Ȓ)+=[]\\{}|;\':",./<>?abcd'


# -----------------------------------------------------------------------
# BENCHMARK
# -----------------------------------------------------------------------
def success(msg):
    print msg


def connected(msg):
    pubnub.publish(crazy, {'Info': 'Connected!'}, error=error, callback=success)


def error(err):
    print err

trips = {'last': None, 'current': None, 'max': 0, 'avg': 0}


def received(message):
    current_trip = trips['current'] = str(datetime.datetime.now())[0:19]
    last_trip = trips['last'] = str(
        datetime.datetime.now() - datetime.timedelta(seconds=1)
    )[0:19]

    # New Trip Span (1 Second)
    if current_trip not in trips:
        trips[current_trip] = 0

        # Average
        if last_trip in trips:
            trips['avg'] = (trips['avg'] + trips[last_trip]) / 2

    # Increment Trip Counter
    trips[current_trip] = trips[current_trip] + 1

    # Update Max
    if trips[current_trip] > trips['max']:
        trips['max'] = trips[current_trip]

    print(message)

    pubnub.publish(crazy, current_trip +
                   " Trip: " +
                   str(trips[current_trip]) +
                   " MAX: " +
                   str(trips['max']) +
                   "/sec " +
                   " AVG: " +
                   str(trips['avg']) +
                   "/sec", error=error)


pubnub.subscribe(crazy, received, connect=connected, error=error)

# -----------------------------------------------------------------------
# IO Event Loop
# -----------------------------------------------------------------------
pubnub.start()
