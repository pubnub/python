## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.1 Real-time Push Cloud API
## -----------------------------------

import sys
import datetime
from Pubnub import PubnubAsync as Pubnub
from functools import partial
from threading import current_thread
import threading
publish_key = len(sys.argv) > 1 and sys.argv[1] or 'demo'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'demo'
secret_key = len(sys.argv) > 3 and sys.argv[3] or 'demo'
cipher_key = len(sys.argv) > 4 and sys.argv[4] or None
ssl_on = len(sys.argv) > 5 and bool(sys.argv[5]) or False

## -----------------------------------------------------------------------
## Initiate Pubnub State
## -----------------------------------------------------------------------
#pubnub = Pubnub( publish_key, subscribe_key, secret_key, cipher_key, ssl_on )
pubnub = Pubnub(publish_key, subscribe_key, secret_key, ssl_on)
crazy = 'hello_world'

current = -1

errors = 0
received = 0

## -----------------------------------------------------------------------
## Subscribe Example
## -----------------------------------------------------------------------


def message_received(message):
    print(message)


def check_received(message):
    global current
    global errors
    global received
    print(message)
    print(current)
    if message <= current:
        print('ERROR')
        #sys.exit()
        errors += 1
    else:
        received += 1
    print('active thread count : ' + str(threading.activeCount()))
    print('errors = ' + str(errors))
    print(current_thread().getName() + ' , ' + 'received = ' + str(received))

    if received != message:
        print('********** MISSED **************** ' + str(message - received))
    current = message


def connected_test(ch):
    print('Connected ' + ch)


def connected(ch):
    pass


'''
pubnub.subscribe({
    'channel'  : 'abcd1',
    'connect'  : connected,
    'callback' : message_received
})
'''


def cb1():
    pubnub.subscribe({
        'channel': 'efgh1',
        'connect': connected,
        'callback': message_received
    })


def cb2():
    pubnub.subscribe({
        'channel': 'dsm-test',
        'connect': connected_test,
        'callback': check_received
    })


def cb3():
    pubnub.unsubscribe({'channel': 'efgh1'})


def cb4():
    pubnub.unsubscribe({'channel': 'abcd1'})


def subscribe(channel):
    pubnub.subscribe({
        'channel': channel,
        'connect': connected,
        'callback': message_received
    })


pubnub.timeout(15, cb1)

pubnub.timeout(30, cb2)


pubnub.timeout(45, cb3)

pubnub.timeout(60, cb4)

#'''
for x in range(1, 1000):
    #print x
    def y(t):
        subscribe('channel-' + str(t))

    def z(t):
        pubnub.unsubscribe({'channel': 'channel-' + str(t)})

    pubnub.timeout(x + 5, partial(y, x))
    pubnub.timeout(x + 25, partial(z, x))
    x += 10
#'''

'''
for x in range(1,1000):
    def cb(r): print r , ' : ', threading.activeCount()
    def y(t):
        pubnub.publish({
            'message' : t,
            'callback' : cb,
            'channel' : 'dsm-test'
        })


    pubnub.timeout(x + 1, partial(y,x))
    x += 1
'''


pubnub.start()
