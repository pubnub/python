

from Pubnub import Pubnub
import time

pubnub = Pubnub("demo","demo")
pubnub_pam = Pubnub("pub-c-c077418d-f83c-4860-b213-2f6c77bde29a", 
	"sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe", "sec-c-OGU3Y2Q4ZWUtNDQwMC00NTI1LThjNWYtNWJmY2M4OGIwNjEy")



# Grant permission read true, write true, on channel ( Async Mode )
def test_1():
	resp = {'response' : None}
	def _callback(response):
		resp['response'] = response

	def _error(response):
		resp['response'] = response

	pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True, write=True, ttl=1, callback=_callback, error=_error)
	time.sleep(2)
	assert resp['response'] == {
									'message': u'Success',
									'payload': {u'auths': {u'abcd': {u'r': 1, u'w': 1}},
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'user', u'channel': u'abcd', u'ttl': 1}
								}
							

# Grant permission read false, write false, on channel ( Async Mode )
def test_2():
	resp = {'response' : None}
	def _callback(response):
		resp['response'] = response

	def _error(response):
		resp['response'] = response

	pubnub_pam.grant(channel="abcd", auth_key="abcd", read=False, write=False, ttl=1, callback=_callback, error=_error)
	time.sleep(2)
	assert resp['response'] == {
									'message': u'Success',
									'payload': {u'auths': {u'abcd': {u'r': 0, u'w': 0}},
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'user', u'channel': u'abcd', u'ttl': 1}
								}


# Grant permission read True, write false, on channel ( Async Mode )
def test_3():
	resp = {'response' : None}
	def _callback(response):
		resp['response'] = response

	def _error(response):
		resp['response'] = response

	pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True, write=False, ttl=1, callback=_callback, error=_error)
	time.sleep(2)
	assert resp['response'] == {
									'message': u'Success',
									'payload': {u'auths': {u'abcd': {u'r': 1, u'w': 0}},
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'user', u'channel': u'abcd', u'ttl': 1}
								}

# Grant permission read False, write True, on channel ( Async Mode )
def test_4():
	resp = {'response' : None}
	def _callback(response):
		resp['response'] = response

	def _error(response):
		resp['response'] = response

	pubnub_pam.grant(channel="abcd", auth_key="abcd", read=False, write=True, ttl=1, callback=_callback, error=_error)
	time.sleep(2)
	assert resp['response'] == {
									'message': u'Success',
									'payload': {u'auths': {u'abcd': {u'r': 0, u'w': 1}},
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'user', u'channel': u'abcd', u'ttl': 1}
								}


# Grant permission read False, write True, on channel ( Async Mode ), TTL 10
def test_5():
	resp = {'response' : None}
	def _callback(response):
		resp['response'] = response

	def _error(response):
		resp['response'] = response

	pubnub_pam.grant(channel="abcd", auth_key="abcd", read=False, write=True, ttl=10, callback=_callback, error=_error)
	time.sleep(2)
	assert resp['response'] == {
									'message': u'Success',
									'payload': {u'auths': {u'abcd': {u'r': 0, u'w': 1}},
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'user', u'channel': u'abcd', u'ttl': 10}
								}


# Grant permission read False, write True, without channel ( Async Mode ), TTL 10
def test_6():
	resp = {'response' : None}
	def _callback(response):
		resp['response'] = response

	def _error(response):
		resp['response'] = response

	pubnub_pam.grant(auth_key="abcd", read=False, write=True, ttl=10, callback=_callback, error=_error)
	time.sleep(2)
	assert resp['response'] == {
									'message': u'Success',
									'payload': { u'r': 0, u'w': 1,
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'subkey', u'ttl': 10}
								}


# Grant permission read False, write False, without channel ( Async Mode )
def test_7():
	resp = {'response' : None}
	def _callback(response):
		resp['response'] = response

	def _error(response):
		resp['response'] = response

	pubnub_pam.grant(auth_key="abcd", read=False, write=False, callback=_callback, error=_error)
	time.sleep(2)
	assert resp['response'] == {
									'message': u'Success',
									'payload': { u'r': 0, u'w': 0,
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'subkey', u'ttl': 1}
								}


# Complete flow , try publish on forbidden channel, grant permission to subkey and try again. ( Sync Mode)

def test_8():
	channel = "test_8-" + str(time.time())
	message = "Hello World"
	auth_key = "auth-" + channel
	pubnub_pam.set_auth_key(auth_key)



	def _cb1(resp, ch=None):
		assert False
	def _err1(resp):
		assert resp['message'] == 'Forbidden'
		assert resp['payload'] == {u'channels': [channel]}
	pubnub_pam.publish(channel=channel,message=message, callback=_cb1, error=_err1)
	time.sleep(2)


	def _cb2(resp, ch=None):
		assert resp == 		{
								'message': u'Success',
								'payload': {u'auths': {auth_key : {u'r': 1, u'w': 1}},
								u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
								u'level': u'user', u'channel': channel, u'ttl': 10}
							}
	def _err2(resp):
		assert False


	resp = pubnub_pam.grant(channel=channel, read=True, write=True, auth_key=auth_key, ttl=10, callback=_cb2, error=_err2)
	time.sleep(2)

	def _cb3(resp, ch=None):
		assert resp[0] == 1
	def _err3(resp):
		assert False

	pubnub_pam.publish(channel=channel,message=message, callback=_cb3, error=_err3)
	time.sleep(2)





# Complete flow , try publish on forbidden channel, grant permission to authkey and try again. 
# then revoke and try again
def test_9():
	channel = "test_9-" + str(time.time())
	message = "Hello World"
	auth_key = "auth-" + channel
	pubnub_pam.set_auth_key(auth_key)

	def _cb1(resp, ch=None):
		assert False
	def _err1(resp):
		assert resp['message'] == 'Forbidden'
		assert resp['payload'] == {u'channels': [channel]}
	pubnub_pam.publish(channel=channel,message=message, callback=_cb1, error=_err1)
	time.sleep(2)


	def _cb2(resp, ch=None):
		assert resp == 		{
								'message': u'Success',
								'payload': {u'auths': {auth_key : {u'r': 1, u'w': 1}},
								u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
								u'level': u'user', u'channel': channel, u'ttl': 10}
							}
	def _err2(resp):
		assert False


	pubnub_pam.grant(channel=channel, read=True, write=True, auth_key=auth_key, ttl=10, callback=_cb2, error=_err2)
	time.sleep(2)

	def _cb3(resp, ch=None):
		assert resp[0] == 1
	def _err3(resp):
		assert False

	pubnub_pam.publish(channel=channel,message=message, callback=_cb3, error=_err3)
	time.sleep(2)

	def _cb4(resp, ch=None):
		assert resp == 		{
								'message': u'Success',
								'payload': {u'auths': {auth_key : {u'r': 0, u'w': 0}},
								u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
								u'level': u'user', u'channel': channel, u'ttl': 1}
							}
	def _err4(resp):
		assert False
	pubnub_pam.revoke(channel=channel, auth_key=auth_key, callback=_cb4, error=_err4)
	time.sleep(2)

	def _cb5(resp, ch=None):
		assert False
	def _err5(resp):
		assert resp['message'] == 'Forbidden'
		assert resp['payload'] == {u'channels': [channel]}
	pubnub_pam.publish(channel=channel,message=message, callback=_cb5, error=_err5)
	time.sleep(2)




# Complete flow , try publish on forbidden channel, grant permission channel level for subkey and try again.
# then revoke and try again
def test_10():
	channel = "test_10-" + str(time.time())
	message = "Hello World"
	auth_key = "auth-" + channel
	pubnub_pam.set_auth_key(auth_key)

	def _cb1(resp, ch=None):
		assert False
	def _err1(resp):
		assert resp['message'] == 'Forbidden'
		assert resp['payload'] == {u'channels': [channel]}
	pubnub_pam.publish(channel=channel,message=message, callback=_cb1, error=_err1)
	time.sleep(2)


	def _cb2(resp, ch=None):
		assert resp == 		{
									'message': u'Success',
									'payload': { u'channels': {channel: {u'r': 1, u'w': 1}},
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'channel', u'ttl': 10}
								}
	def _err2(resp):
		assert False


	pubnub_pam.grant(channel=channel, read=True, write=True, ttl=10, callback=_cb2, error=_err2)
	time.sleep(2)

	def _cb3(resp, ch=None):
		assert resp[0] == 1
	def _err3(resp):
		assert False

	pubnub_pam.publish(channel=channel,message=message, callback=_cb3, error=_err3)
	time.sleep(2)

	def _cb4(resp, ch=None):
		assert resp == 		{
									'message': u'Success',
									'payload': { u'channels': {channel : {u'r': 0, u'w': 0}},
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'channel', u'ttl': 1}
								}
	def _err4(resp):
		assert False
	pubnub_pam.revoke(channel=channel, callback=_cb4, error=_err4)
	time.sleep(2)

	def _cb5(resp, ch=None):
		assert False
	def _err5(resp):
		assert resp['message'] == 'Forbidden'
		assert resp['payload'] == {u'channels': [channel]}
	pubnub_pam.publish(channel=channel,message=message, callback=_cb5, error=_err5)
	time.sleep(2)



# Complete flow , try publish on forbidden channel, grant permission subkey level for subkey and try again.
# then revoke and try again
def test_11():
	channel = "test_11-" + str(time.time())
	message = "Hello World"
	auth_key = "auth-" + channel
	pubnub_pam.set_auth_key(auth_key)

	def _cb1(resp, ch=None):
		assert False
	def _err1(resp):
		assert resp['message'] == 'Forbidden'
		assert resp['payload'] == {u'channels': [channel]}
	pubnub_pam.publish(channel=channel,message=message, callback=_cb1, error=_err1)
	time.sleep(2)


	def _cb2(resp, ch=None):
		assert resp == 		{
									'message': u'Success',
									'payload': { u'r': 1, u'w': 1,
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'subkey', u'ttl': 10}
								}
	def _err2(resp):
		assert False


	pubnub_pam.grant(read=True, write=True, ttl=10, callback=_cb2, error=_err2)
	time.sleep(2)

	def _cb3(resp, ch=None):
		assert resp[0] == 1
	def _err3(resp):
		assert False

	pubnub_pam.publish(channel=channel,message=message, callback=_cb3, error=_err3)
	time.sleep(2)

	def _cb4(resp, ch=None):
		assert resp == 		{
									'message': u'Success',
									'payload': {u'r': 0, u'w': 0,
									u'subscribe_key': u'sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe',
									u'level': u'subkey', u'ttl': 1}
								}
	def _err4(resp):
		assert False
	pubnub_pam.revoke(callback=_cb4, error=_err4)
	time.sleep(2)

	def _cb5(resp, ch=None):
		assert False
	def _err5(resp):
		assert resp['message'] == 'Forbidden'
		assert resp['payload'] == {u'channels': [channel]}
	pubnub_pam.publish(channel=channel,message=message, callback=_cb5, error=_err5)
	time.sleep(2)
