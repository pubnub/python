## www.pubnub.com - PubNub Real-time push service in the cloud. 
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/

## -----------------------------------
## PubNub 3.1 Real-time Push Cloud API
## -----------------------------------

import sys
import time
import random
sys.path.append('../')
sys.path.append('./')
sys.path.append('../common/')
from Pubnub import Pubnub

publish_key   = len(sys.argv) > 1 and sys.argv[1] or 'demo'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'demo'
secret_key    = len(sys.argv) > 3 and sys.argv[3] or None 
cipher_key    = len(sys.argv) > 4 and sys.argv[4] or None
ssl_on        = len(sys.argv) > 5 and bool(sys.argv[5]) or False

## -----------------------------------------------------------------------
## Initiat Class
## -----------------------------------------------------------------------
pubnub = Pubnub( publish_key, subscribe_key, secret_key, cipher_key, ssl_on )
ch = 'python-async-test-channel-'
expect = 0
done = 0
failures = 0
passes = 0

def stop():
    global done
    global count
    pubnub.stop()
    print "============================"
    print 'Total\t:\t' , failures + passes
    print 'PASS\t:\t' , passes
    print 'FAIL\t:\t', failures
    print "============================"

## ---------------------------------------------------------------------------
## Unit Test Function
## ---------------------------------------------------------------------------
def test( trial, name ) :
    global failures
    global passes
    global done
    done += 1
    #print trial
    if trial == False:
        print 'FAIL : ', name
        failures += 1
    else:
        print 'PASS : ', name
        passes += 1
    if done == expect:
        stop()

def test_publish():
    channel = ch + str(random.random())
    def publish_cb(messages):
        test(messages[0] == 1, "Publish Test")

    pubnub.publish({
        'channel' : channel,
        'message' :  {'one': 'Hello World! --> ɂ顶@#$%^&*()!', 'two': 'hello2'},
        'callback' : publish_cb
    }) 


def test_history():
    channel = ch + str(random.random())
    def history_cb(messages):
        test(len(messages) <= 1, "History Test")    
    pubnub.history({
        'channel' : channel,
        'limit' :  1,
        'callback' : history_cb 
    })



def test_subscribe():
    message = "Testing Subscribe " + str(random.random())
    channel = ch + str(random.random())
    def subscribe_connect_cb():
        def publish_cb(response):
            test(response[0] == 1, 'Publish Test in subscribe Connect Callback')
        pubnub.publish({
            'channel'  :  channel,
            'message'  :  message,
            'callback' : publish_cb
        })
    def subscribe_cb(response):
        test(response == message , 'Subscribe Receive Test in subscribe Callback')
    pubnub.subscribe({
        'channel' : channel,
        'connect' : subscribe_connect_cb,
        'callback': subscribe_cb
    }) 
    

def test_here_now():
    channel = ch + str(random.random()) 
    message = "Testing Subscribe"
    def subscribe_connect_cb():
        def here_now_cb(response):
            test(response["occupancy"] > 0, 'Here Now Test')
            def publish_cb(response):
                test(response[0] == 1, 'Here Now Test: Publish Test in subscribe Connect Callback')
            pubnub.publish({
                'channel'  : channel,
                'message'  : message,
                'callback' : publish_cb
            })
        time.sleep(5)
        pubnub.here_now({
            'channel' : channel,
            'callback' : here_now_cb
        })


    def subscribe_cb(response):
        test(response == message , 'Here Now Test: Subscribe Receive Test in subscribe Callback')
    pubnub.subscribe({
        'channel' : channel,
        'connect' : subscribe_connect_cb,
        'callback': subscribe_cb
    }) 

expect = 7
test_publish()
test_history()
test_subscribe()
test_here_now()



pubnub.start()
if failures > 0:
    raise Exception('Fail', failures)
