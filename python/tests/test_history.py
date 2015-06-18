from pubnub import Pubnub
import time
import random
from nose.tools import with_setup


pubnub = Pubnub("ds","ds")
pubnub_enc = Pubnub(publish_key="ds",subscribe_key="ds",cipher_key="enigma")


def rand(msg):
	return "rand-" + str(random.random()) + "-" + msg

channel = rand("channel")
channel_enc = rand("channel_enc")

messages = []


def setup_func():
     for i in range(0,20):
     	msg = rand("message-" + str(i))
     	messages.append(msg)
     	pubnub.publish(channel=channel, message=msg)
     	pubnub_enc.publish(channel=channel_enc, message=msg)


@with_setup(setup_func)
def test_1():
	time.sleep(3)
	hresp = pubnub.history(channel=channel, count=20)
	hresp2 = pubnub_enc.history(channel=channel_enc, count=20)
	assert hresp[0] == messages
	assert hresp2[0] == messages



