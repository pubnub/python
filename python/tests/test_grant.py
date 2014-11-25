

from Pubnub import Pubnub
import time

pubnub = Pubnub("demo","demo")
pubnub_pam = Pubnub("pam", 
	"pam", "pam")


# Grant permission read true, write true, on channel ( Sync Mode )
def test_1():
	resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True, write=True, ttl=1)
	print resp
	assert resp['message'] == 'Success'
	assert resp['payload'] == {
								'auths': {'abcd': {'r': 1, 'w': 1, 'm' : 0}},
								'subscribe_key': 'pam',
								'level': 'user', 'channel': 'abcd', 'ttl': 1
							  }
							

# Grant permission read false, write false, on channel ( Sync Mode )
def test_2():
	resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=False, write=False, ttl=1)
	assert resp['message'] == 'Success'
	assert resp['payload'] == {
								'auths': {'abcd': {'r': 0, 'w': 0, 'm' : 0}},
								'subscribe_key': 'pam',
								'level': 'user', 'channel': 'abcd', 'ttl': 1
							  }

# Grant permission read True, write false, on channel ( Sync Mode )
def test_3():
	resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True, write=False, ttl=1)
	assert resp['message'] == 'Success'
	assert resp['payload'] == {
								'auths': {'abcd': {'r': 1, 'w': 0, 'm' : 0}},
								'subscribe_key': 'pam',
								'level': 'user', 'channel': 'abcd', 'ttl': 1
							  }

# Grant permission read False, write True, on channel ( Sync Mode )
def test_4():
	resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True, write=False, ttl=1)
	assert resp['message'] == 'Success'
	assert resp['payload'] == {
								'auths': {'abcd': {'r': 1, 'w': 0, 'm' : 0}},
								'subscribe_key': 'pam',
								'level': 'user', 'channel': 'abcd', 'ttl': 1
							  }

# Grant permission read False, write True, on channel ( Sync Mode ), TTL 10
def test_5():
	resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True, write=False, ttl=10)
	assert resp['message'] == 'Success'
	assert resp['payload'] == {
								'auths': {'abcd': {'r': 1, 'w': 0, 'm' : 0}},
								'subscribe_key': 'pam',
								'level': 'user', 'channel': 'abcd', 'ttl': 10
							  }

# Grant permission read False, write True, without channel ( Sync Mode ), TTL 10
def test_6():
	resp = pubnub_pam.grant(auth_key="abcd", read=True, write=False, ttl=10)
	assert resp['message'] == 'Success'
	assert resp['payload'] == {
								'subscribe_key': 'pam',
								'level': 'subkey' , u'r': 1, u'w': 0, 'm' : 0, 'ttl': 10
							  }


# Grant permission read False, write False, without channel ( Sync Mode )
def test_7():
	resp = pubnub_pam.grant(auth_key="abcd", read=False, write=False)
	assert resp['message'] == 'Success'
	assert resp['payload'] == {
								'subscribe_key': 'pam',
								'level': 'subkey' , u'r': 0, u'w': 0, 'm' : 0, 'ttl': 1
							  }


# Complete flow , try publish on forbidden channel, grant permission to auth key and try again. ( Sync Mode)

def test_8():
	channel = "test_8-" + str(time.time())
	message = "Hello World"
	auth_key = "auth-" + channel
	pubnub_pam.set_auth_key(auth_key)
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp['message'] == 'Forbidden'
	assert resp['payload'] == {u'channels': [channel]}
	resp = pubnub_pam.grant(channel=channel, read=True, write=True, auth_key=auth_key, ttl=10)
	assert resp == 			{
								'message': u'Success',
								'payload': {u'auths': {auth_key : {u'r': 1, u'w': 1, 'm' : 0}},
								u'subscribe_key': u'pam',
								u'level': u'user', u'channel': channel, u'ttl': 10}
							}
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp[0] == 1


# Complete flow , try publish on forbidden channel, grant permission to authkey and try again. ( Sync Mode)
# then revoke and try again
def test_9():
	channel = "test_9-" + str(time.time())
	message = "Hello World"
	auth_key = "auth-" + channel
	pubnub_pam.set_auth_key(auth_key)
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp['message'] == 'Forbidden'
	assert resp['payload'] == {u'channels': [channel]}
	resp = pubnub_pam.grant(channel=channel, read=True, write=True, auth_key=auth_key, ttl=10)
	print resp
	assert resp == 			{
								'message': u'Success',
								'payload': {u'auths': {auth_key : {u'r': 1, u'w': 1, 'm' : 0}},
								u'subscribe_key': u'pam',
								u'level': u'user', u'channel': channel, u'ttl': 10}
							}
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp[0] == 1
	resp = pubnub_pam.revoke(channel=channel, auth_key=auth_key)
	print resp
	assert resp == 			{
								'message': u'Success',
								'payload': {u'auths': {auth_key : {u'r': 0, u'w': 0, 'm' : 0}},
								u'subscribe_key': u'pam',
								u'level': u'user', u'channel': channel, u'ttl': 1}
							}
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp['message'] == 'Forbidden'
	assert resp['payload'] == {u'channels': [channel]}

# Complete flow , try publish on forbidden channel, grant permission channel level for subkey and try again. ( Sync Mode)
# then revoke and try again
def test_10():
	channel = "test_10-" + str(time.time())
	message = "Hello World"
	auth_key = "auth-" + channel
	pubnub_pam.set_auth_key(auth_key)
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp['message'] == 'Forbidden'
	assert resp['payload'] == {u'channels': [channel]}
	resp = pubnub_pam.grant(channel=channel, read=True, write=True, ttl=10)
	print resp
	assert resp == 			{
									'message': u'Success',
									'payload': { u'channels': {channel: {u'r': 1, u'w': 1, 'm' : 0}},
									u'subscribe_key': u'pam',
									u'level': u'channel', u'ttl': 10}
								}
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp[0] == 1
	resp = pubnub_pam.revoke(channel=channel)
	print resp
	assert resp == 			{
									'message': u'Success',
									'payload': { u'channels': {channel : {u'r': 0, u'w': 0, 'm' : 0}},
									u'subscribe_key': u'pam',
									u'level': u'channel', u'ttl': 1}
								}
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp['message'] == 'Forbidden'
	assert resp['payload'] == {u'channels': [channel]}

# Complete flow , try publish on forbidden channel, grant permission subkey level for subkey and try again. ( Sync Mode)
# then revoke and try again
def test_11():
	channel = "test_11-" + str(time.time())
	message = "Hello World"
	auth_key = "auth-" + channel
	pubnub_pam.set_auth_key(auth_key)
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp['message'] == 'Forbidden'
	assert resp['payload'] == {u'channels': [channel]}
	resp = pubnub_pam.grant(read=True, write=True, ttl=10)
	print resp
	assert resp == 			{
									'message': u'Success',
									'payload': { u'r': 1, u'w': 1, 'm' : 0,
									u'subscribe_key': u'pam',
									u'level': u'subkey', u'ttl': 10}
								}
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp[0] == 1
	resp = pubnub_pam.revoke()
	print resp
	assert resp == 			{
									'message': u'Success',
									'payload': {u'r': 0, u'w': 0, 'm' : 0,
									u'subscribe_key': u'pam',
									u'level': u'subkey', u'ttl': 1}
								}
	resp = pubnub_pam.publish(channel=channel,message=message)
	assert resp['message'] == 'Forbidden'
	assert resp['payload'] == {u'channels': [channel]}


