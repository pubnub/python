import time

from pubnub import PubnubTwisted as Pubnub

subkey = "sub-c-9aeec0d4-cdf4-11e5-bcee-0619f8945a4f"
pubkey = "pub-c-b3fdf8fc-4516-4ab2-8836-6fb22ba7870d"
secretkey = "sec-c-ZDQwNTUwMDctZDViYi00MzhlLTg2NTctYjViZDcwNTA5Zjhj"
pubnub = Pubnub(pubkey, subkey)
pubnub_pam = Pubnub(pubkey, subkey, secretkey)


# Grant permission read true, write true, on channel ( Async Mode )
def test_1():
    def _callback(resp, ch=None):
        assert resp == {
            'message': u'Success',
            'payload': {u'auths': {u'abcd': {u'r': 1, u'w': 1}},
                        u'subscribe_key': subkey,
                        u'level': u'user', u'channel': u'abcd', u'ttl': 1}
        }

    def _error(response):
        assert False

    pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True, write=True, ttl=1, callback=_callback, error=_error)


# Grant permission read false, write false, on channel ( Async Mode )
def test_2():
    def _callback(resp, ch=None):
        assert resp == {
            'message': u'Success',
            'payload': {u'auths': {u'abcd': {u'r': 0, u'm': 0, u'w': 0}},
                        u'subscribe_key': subkey,
                        u'level': u'user', u'channel': u'abcd', u'ttl': 1}
        }

    def _error(response):
        print("error")
        print(response)
        assert False

    pubnub_pam.grant(channel="abcd", auth_key="abcd", read=False, write=False, ttl=1, callback=_callback, error=_error)


# Grant permission read True, write false, on channel ( Async Mode )
def test_3():
    def _callback(resp, ch=None):
        assert resp == {
            'message': u'Success',
            'payload': {u'auths': {u'abcd': {u'r': 1, u'm': 0, u'w': 0}},
                        u'subscribe_key': subkey,
                        u'level': u'user', u'channel': u'abcd', u'ttl': 1}
        }

    def _error(response):
        assert False

    pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True, write=False, ttl=1, callback=_callback, error=_error)


# Grant permission read False, write True, on channel ( Async Mode )
def test_4():
    def _callback(resp, ch=None):
        assert resp == {
            'message': u'Success',
            'payload': {u'auths': {u'abcd': {u'r': 0, u'm': 0, u'w': 1}},
                        u'subscribe_key': subkey,
                        u'level': u'user', u'channel': u'abcd', u'ttl': 1}
        }

    def _error(response):
        assert False

    pubnub_pam.grant(channel="abcd", auth_key="abcd", read=False, write=True, ttl=1, callback=_callback, error=_error)


# Grant permission read False, write True, on channel ( Async Mode ), TTL 10
def test_5():
    def _callback(resp, ch=None):
        assert resp == {
            'message': u'Success',
            'payload': {u'auths': {u'abcd': {u'r': 0, u'm': 0, u'w': 1}},
                        u'subscribe_key': subkey,
                        u'level': u'user', u'channel': u'abcd', u'ttl': 10}
        }

    def _error(response):
        assert False

    pubnub_pam.grant(channel="abcd", auth_key="abcd", read=False, write=True, ttl=10, callback=_callback, error=_error)


# Grant permission read False, write True, without channel ( Async Mode ), TTL 10
def test_6():
    def _callback(resp, ch=None):
        assert resp == {
            'message': u'Success',
            'payload': {u'r': 0, u'm': 0, u'w': 1,
                        u'subscribe_key': subkey,
                        u'level': u'subkey', u'ttl': 10}
        }

    def _error(response):
        print(response)
        assert False

    pubnub_pam.grant(read=False, write=True, ttl=10, callback=_callback, error=_error)


# Grant permission read False, write False, without channel ( Async Mode )
def test_7():
    def _callback(resp, ch=None):
        assert resp == {
            'message': u'Success',
            'payload': {u'r': 0, u'm': 0, u'w': 0,
                        u'subscribe_key': subkey,
                        u'level': u'subkey', u'ttl': 1}
        }

    def _error(response):
        assert False

    pubnub_pam.grant(read=False, write=False, callback=_callback, error=_error)


# Complete flow , try publish on forbidden channel, grant permission to subkey and try again. ( Sync Mode)

def test_8():
    channel = "test_8-" + str(time.time())
    message = "Hello World"
    auth_key = "auth-" + channel
    pubnub.set_auth_key(auth_key)

    def _cb2(resp, ch=None):
        assert resp == {
            'message': u'Success',
            'payload': {u'auths': {auth_key: {u'r': 1, u'm': 0, u'w': 1}},
                        u'subscribe_key': subkey,
                        u'level': u'user', u'channel': channel, u'ttl': 10}
        }

        def _cb3(resp, ch=None):
            assert resp[0] == 1

        def _err3(resp):
            print(resp)
            assert False

        time.sleep(7)
        pubnub.publish(channel=channel, message=message, callback=_cb3, error=_err3)

    def _err2(resp):
        assert False

    pubnub_pam.grant(channel=channel, read=True, write=True, auth_key=auth_key, ttl=10, callback=_cb2, error=_err2)


# Complete flow , try publish on forbidden channel, grant permission to authkey and try again.
# then revoke and try again
def test_9():
    channel = "test_9-" + str(time.time())
    message = "Hello World"
    auth_key = "auth-" + channel
    pubnub.set_auth_key(auth_key)

    def _cb2(resp, ch=None):
        assert resp == {
            'message': u'Success',
            'payload': {u'auths': {auth_key: {u'r': 1, u'm': 0, u'w': 1}},
                        u'subscribe_key': subkey,
                        u'level': u'user', u'channel': channel, u'ttl': 10}
        }

        def _cb3(resp, ch=None):
            assert resp[0] == 1

            def _cb4(resp, ch=None):
                assert resp == {
                    'message': u'Success',
                    'payload': {u'auths': {auth_key: {u'r': 0, u'm': 0, u'w': 0}},
                                u'subscribe_key': subkey,
                                u'level': u'user', u'channel': channel, u'ttl': 1}
                }

                def _cb5(resp, ch=None):
                    print(resp)
                    assert False

                def _err5(resp):
                    assert resp['message'] == 'Forbidden'
                    assert resp['payload'] == {u'channels': [channel]}

                time.sleep(5)
                pubnub.publish(channel=channel, message=message, callback=_cb5, error=_err5)

            def _err4(resp):
                assert False

            pubnub_pam.revoke(channel=channel, auth_key=auth_key, callback=_cb4, error=_err4)

        def _err3(resp):
            assert False

        time.sleep(7)
        pubnub.publish(channel=channel, message=message, callback=_cb3, error=_err3)

    def _err2(resp):
        assert False

    pubnub_pam.grant(channel=channel, read=True, write=True, auth_key=auth_key, ttl=10, callback=_cb2, error=_err2)


# Complete flow , try publish on forbidden channel, grant permission channel level for subkey and try again.
# then revoke and try again
def test_10():
    channel = "test_10-" + str(time.time())
    message = "Hello World"
    auth_key = "auth-" + channel
    pubnub.set_auth_key(auth_key)

    def _cb1(resp, ch=None):
        assert False

    def _err1(resp):
        assert resp['message'] == 'Forbidden'
        assert resp['payload'] == {u'channels': [channel]}

        def _cb2(resp, ch=None):
            assert resp == {
                'message': u'Success',
                'payload': {u'channels': {channel: {u'r': 1, u'm': 0, u'w': 1}},
                            u'subscribe_key': subkey,
                            u'level': u'channel', u'ttl': 10}
            }

            def _cb3(resp, ch=None):
                assert resp[0] == 1

                def _cb4(resp, ch=None):
                    assert resp == {
                        'message': u'Success',
                        'payload': {u'channels': {channel: {u'r': 0, u'm': 0, u'w': 0}},
                                    u'subscribe_key': subkey,
                                    u'level': u'channel', u'ttl': 1}
                    }

                    def _cb5(resp, ch=None):
                        print(resp)
                        assert False

                    def _err5(resp):
                        assert resp['message'] == 'Forbidden'
                        assert resp['payload'] == {u'channels': [channel]}

                    time.sleep(5)
                    pubnub.publish(channel=channel, message=message, callback=_cb5, error=_err5)

                def _err4(resp):
                    assert False

                pubnub_pam.revoke(channel=channel, callback=_cb4, error=_err4)

            def _err3(resp):
                assert False

            time.sleep(5)
            pubnub.publish(channel=channel, message=message, callback=_cb3, error=_err3)

        def _err2(resp):
            assert False

        pubnub_pam.grant(channel=channel, read=True, write=True, ttl=10, callback=_cb2, error=_err2)

    pubnub.publish(channel=channel, message=message, callback=_cb1, error=_err1)


# Complete flow , try publish on forbidden channel, grant permission subkey level for subkey and try again.
# then revoke and try again
def test_11():
    channel = "test_11-" + str(time.time())
    message = "Hello World"
    auth_key = "auth-" + channel
    pubnub.set_auth_key(auth_key)

    def _cb2(resp, ch=None):
        print(resp)
        assert resp == {
            'message': u'Success',
            'payload': {u'r': 1, u'm': 0, u'w': 1,
                        u'subscribe_key': subkey,
                        u'level': u'subkey', u'ttl': 10}
        }

        def _cb3(resp, ch=None):
            assert resp[0] == 1

            def _cb4(resp, ch=None):
                assert resp == {
                    'message': u'Success',
                    'payload': {u'r': 0, u'm': 0, u'w': 0,
                                u'subscribe_key': subkey,
                                u'level': u'subkey', u'ttl': 1}
                }

                def _cb5(resp, ch=None):
                    assert False

                def _err5(resp):
                    assert resp['message'] == 'Forbidden'
                    assert resp['payload'] == {u'channels': [channel]}

                time.sleep(5)
                pubnub.publish(channel=channel, message=message, callback=_cb5, error=_err5)

            def _err4(resp):
                assert False

            pubnub_pam.revoke(callback=_cb4, error=_err4)

        def _err3(resp):
            assert False

        time.sleep(5)
        pubnub.publish(channel=channel, message=message, callback=_cb3, error=_err3)

    def _err2(resp):
        assert False

    pubnub_pam.grant(read=True, write=True, ttl=10, callback=_cb2, error=_err2)


x = 5


def run_test(t):
    global x
    x += 5
    i = (x / 5) - 1

    def _print():
        print('Running test ' + str(i))

    pubnub.timeout(x, _print)
    pubnub.timeout(x + 1, t)


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

pubnub_pam.start()
