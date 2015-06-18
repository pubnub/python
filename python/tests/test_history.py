from pubnub import Pubnub
import time
import random
from nose.tools import with_setup


pubnub = Pubnub("ds","ds")
pubnub_enc = Pubnub(publish_key="ds",subscribe_key="ds",cipher_key="enigma")
pubnub_pam = Pubnub(publish_key="pam", subscribe_key="pam", secret_key="pam")


def rand(msg):
	return "rand-" + str(random.random()) + "-" + msg

channel = rand("channel")
channel_enc = rand("channel_enc")
channel_pam = rand("channel_pam")

messages = []


def setup_func():
     for i in range(0,20):
     	msg = rand("message-" + str(i))
     	messages.append(msg)
     	pubnub_pam.grant(channel=channel_pam, read=True, write=True, ttl=144000)
     	pubnub.publish(channel=channel, message=msg)
     	pubnub_enc.publish(channel=channel_enc, message=msg)
     	pubnub_pam.publish(channel=channel_pam, message=msg)


@with_setup(setup_func)
def test_1():
	time.sleep(3)
	hresp = pubnub.history(channel=channel, count=20)
	hresp2 = pubnub_enc.history(channel=channel_enc, count=20)
	hresp3 = pubnub_pam.history(channel=channel_pam, count=20)
	hresp4 = pubnub_pam.history(channel=channel_pam + "no_rw", count=20)
	assert hresp[0] == messages
	assert hresp2[0] == messages
	assert hresp3[0] == messages
	assert hresp4['message'] == 'Forbidden'
	assert channel_pam + "no_rw" in hresp4['payload']['channels']



