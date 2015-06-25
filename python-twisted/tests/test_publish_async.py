

from pubnub import PubnubTwisted as Pubnub
import time

pubnub = Pubnub("demo","demo")
pubnub_enc = Pubnub("demo", "demo", cipher_key="enigma")
pubnub_pam = Pubnub("pub-c-c077418d-f83c-4860-b213-2f6c77bde29a", 
	"sub-c-e8839098-f568-11e2-a11a-02ee2ddab7fe", "sec-c-OGU3Y2Q4ZWUtNDQwMC00NTI1LThjNWYtNWJmY2M4OGIwNjEy")



# Publish and receive string
def test_1():

	channel = "test_1-" + str(time.time())
	message = "I am a string"

	def _cb(resp, ch=None):
		assert resp == message
		pubnub.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive array
def test_2():

	channel = "test_2-" + str(time.time())
	message = [1,2]

	def _cb(resp, ch=None):
		assert resp == message
		pubnub.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive json object
def test_3():

	channel = "test_2-" + str(time.time())
	message = { "a" : "b" }

	def _cb(resp, ch=None):
		assert resp == message
		pubnub.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive number
def test_4():

	channel = "test_2-" + str(time.time())
	message = 100

	def _cb(resp, ch=None):
		assert resp == message
		pubnub.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive number string
def test_5():

	channel = "test_5-" + str(time.time())
	message = "100"

	def _cb(resp, ch=None):
		assert resp == message
		pubnub.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub.subscribe(channel, callback=_cb, connect=_connect, error=_error)


# Publish and receive string (Encryption enabled)
def test_6():

	channel = "test_6-" + str(time.time())
	message = "I am a string"

	def _cb(resp, ch=None):
		assert resp == message
		pubnub_enc.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub_enc.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub_enc.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive array (Encryption enabled)
def test_7():

	channel = "test_7-" + str(time.time())
	message = [1,2]

	def _cb(resp, ch=None):
		assert resp == message
		pubnub_enc.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub_enc.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub_enc.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive json object (Encryption enabled)
def test_8():

	channel = "test_8-" + str(time.time())
	message = { "a" : "b" }

	def _cb(resp, ch=None):
		assert resp == message
		pubnub_enc.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub_enc.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub_enc.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive number (Encryption enabled)
def test_9():

	channel = "test_9-" + str(time.time())
	message = 100

	def _cb(resp, ch=None):
		assert resp == message
		pubnub_enc.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub_enc.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub_enc.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive number string (Encryption enabled)
def test_10():

	channel = "test_10-" + str(time.time())
	message = "100"

	def _cb(resp, ch=None):
		assert resp == message
		pubnub_enc.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub_enc.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub_enc.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive object string (Encryption enabled)
def test_11():

	channel = "test_11-" + str(time.time())
	message = '{"a" : "b"}'

	def _cb(resp, ch=None):
		assert resp == message
		pubnub_enc.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub_enc.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub_enc.subscribe(channel, callback=_cb, connect=_connect, error=_error)

# Publish and receive array string (Encryption enabled)
def test_12():

	channel = "test_12-" + str(time.time())
	message = '[1,2]'

	def _cb(resp, ch=None):
		assert resp == message
		pubnub_enc.unsubscribe(channel)

	def _connect(resp):
		def _cb1(resp,ch=None):
			assert resp[0] == 1
		def _err1(resp):
			assert False
		pubnub_enc.publish(channel,message, callback=_cb1, error=_err1)

	def _error(resp):
		assert False

	pubnub_enc.subscribe(channel, callback=_cb, connect=_connect, error=_error)

x = 5
def run_test(t):
	global x
	x += 5
	i = (x / 5) - 1
	def _print():
		print('Running test ' + str(i))
	pubnub.timeout(x, _print)
	pubnub.timeout(x + 1,t)

def stop():
	pubnub.stop()

run_test(test_1)
run_test(test_2)
run_test(test_3)
run_test(test_4)
run_test(test_5)
run_test(test_6)
run_test(test_7)
run_test(test_8)
run_test(test_9)
run_test(test_10)
run_test(test_11)
run_test(stop)

pubnub_enc.start()
