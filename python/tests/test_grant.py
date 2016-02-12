from pubnub import Pubnub
import time

subkey = "sub-c-9aeec0d4-cdf4-11e5-bcee-0619f8945a4f"
pubkey = "pub-c-b3fdf8fc-4516-4ab2-8836-6fb22ba7870d"
secretkey = "sec-c-ZDQwNTUwMDctZDViYi00MzhlLTg2NTctYjViZDcwNTA5Zjhj"
pubnub = Pubnub(pubkey, subkey)
pubnub_pam = Pubnub(pubkey, subkey, secretkey)
pam_timeout = 10


# Grant permission read true, write true, on channel ( Sync Mode )
def test_1():
    resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True,
                            write=True, ttl=1)
    print resp
    assert resp['message'] == 'Success'
    assert resp['payload'] == {
        'auths': {'abcd': {'r': 1, 'w': 1, 'm': 0}},
        'subscribe_key': subkey,
        'level': 'user', 'channel': 'abcd', 'ttl': 1
    }


# Grant permission read false, write false, on channel ( Sync Mode )
def test_2():
    resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=False,
                            write=False, ttl=1)
    assert resp['message'] == 'Success'
    assert resp['payload'] == {
        'auths': {'abcd': {'r': 0, 'w': 0, 'm': 0}},
        'subscribe_key': subkey,
        'level': 'user', 'channel': 'abcd', 'ttl': 1
    }


# Grant permission read True, write false, on channel ( Sync Mode )
def test_3():
    resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True,
                            write=False, ttl=1)
    assert resp['message'] == 'Success'
    assert resp['payload'] == {
        'auths': {'abcd': {'r': 1, 'w': 0, 'm': 0}},
        'subscribe_key': subkey,
        'level': 'user', 'channel': 'abcd', 'ttl': 1
    }


# Grant permission read False, write True, on channel ( Sync Mode )
def test_4():
    resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True,
                            write=False, ttl=1)
    assert resp['message'] == 'Success'
    assert resp['payload'] == {
        'auths': {'abcd': {'r': 1, 'w': 0, 'm': 0}},
        'subscribe_key': subkey,
        'level': 'user', 'channel': 'abcd', 'ttl': 1
    }


# Grant permission read False, write True, on channel ( Sync Mode ), TTL 10
def test_5():
    resp = pubnub_pam.grant(channel="abcd", auth_key="abcd", read=True,
                            write=False, ttl=10)
    assert resp['message'] == 'Success'
    assert resp['payload'] == {
        'auths': {'abcd': {'r': 1, 'w': 0, 'm': 0}},
        'subscribe_key': subkey,
        'level': 'user', 'channel': 'abcd', 'ttl': 10
    }


# Complete flow , try publish on forbidden channel, grant permission to
# auth key and try again. ( Sync Mode)
def test_8():
    channel = "test_8-" + str(time.time())
    message = "Hello World"
    auth_key = "auth-" + channel
    pubnub.set_auth_key(auth_key)
    resp = pubnub_pam.grant(channel=channel, read=True, write=True,
                            auth_key=auth_key, ttl=10)
    assert resp == {
        'message': u'Success',
        'payload': {u'auths': {auth_key: {u'r': 1, u'w': 1, 'm': 0}},
                    u'subscribe_key': subkey,
                    u'level': u'user', u'channel': channel, u'ttl': 10}
    }
    time.sleep(pam_timeout)
    resp = pubnub.publish(channel=channel, message=message)
    assert resp[0] == 1


# Complete flow , try publish on forbidden channel, grant permission to authkey
# and try again. ( Sync Mode) then revoke and try again
def test_9():
    channel = "test_9-" + str(time.time())
    message = "Hello World"
    auth_key = "auth-" + channel
    pubnub.set_auth_key(auth_key)
    pubnub_pam.revoke()
    resp = pubnub_pam.grant(channel=channel, read=True, write=True,
                            auth_key=auth_key, ttl=10)
    print resp
    assert resp == {
        'message': u'Success',
        'payload': {u'auths': {auth_key: {u'r': 1, u'w': 1, 'm': 0}},
                    u'subscribe_key': subkey,
                    u'level': u'user', u'channel': channel, u'ttl': 10}
    }
    time.sleep(pam_timeout)
    resp = pubnub.publish(channel=channel, message=message)
    assert resp[0] == 1
    resp = pubnub_pam.revoke(channel=channel, auth_key=auth_key)
    print resp
    assert resp == {
        'message': u'Success',
        'payload': {u'auths': {auth_key: {u'r': 0, u'w': 0, 'm': 0}},
                    u'subscribe_key': subkey,
                    u'level': u'user', u'channel': channel, u'ttl': 1}
    }
    time.sleep(pam_timeout)
    resp = pubnub.publish(channel=channel, message=message)
    assert resp['message'] == 'Forbidden'
    assert resp['payload'] == {u'channels': [channel]}


# Complete flow , try publish on forbidden channel, grant permission channel
# level for subkey and try again. ( Sync Mode) then revoke and try again
def test_10():
    channel = "test_10-" + str(time.time())
    message = "Hello World"
    resp = pubnub_pam.grant(channel=channel, read=True, write=True, ttl=10)
    assert resp == {
        'message': u'Success',
        'payload': {u'channels': {channel: {u'r': 1, u'w': 1, 'm': 0}},
                    u'subscribe_key': subkey,
                    u'level': u'channel', u'ttl': 10}
    }
    time.sleep(pam_timeout)
    resp = pubnub.publish(channel=channel, message=message)
    assert resp[0] == 1
    resp = pubnub_pam.revoke(channel=channel)
    assert resp == {
        'message': u'Success',
        'payload': {u'channels': {channel: {u'r': 0, u'w': 0, 'm': 0}},
                    u'subscribe_key': subkey,
                    u'level': u'channel', u'ttl': 1}
    }
    time.sleep(pam_timeout)
    resp = pubnub.publish(channel=channel, message=message)
    assert resp['message'] == 'Forbidden'
    assert resp['payload'] == {u'channels': [channel]}


# Complete flow , try publish on forbidden channel, grant permission subkey
# level for subkey and try again. ( Sync Mode) then revoke and try again
def test_11():
    channel = "test_11-" + str(time.time())
    message = "Hello World"
    pubnub_pam.revoke()
    resp = pubnub_pam.grant(read=True, write=True, ttl=10)
    print resp
    assert resp == {
        'message': u'Success',
        'payload': {u'r': 1, u'w': 1, 'm': 0,
                    u'subscribe_key': subkey,
                    u'level': u'subkey', u'ttl': 10}
    }
    time.sleep(pam_timeout)
    resp = pubnub_pam.audit()
    print resp
    resp = pubnub.publish(channel=channel, message=message)
    print resp
    assert resp[0] == 1
    resp = pubnub_pam.revoke()
    print resp
    assert resp == {
        'message': u'Success',
        'payload': {u'r': 0, u'w': 0, 'm': 0,
                    u'subscribe_key': subkey,
                    u'level': u'subkey', u'ttl': 1}
    }
    time.sleep(pam_timeout)
    resp = pubnub.publish(channel=channel, message=message)
    assert resp['message'] == 'Forbidden'
    assert resp['payload'] == {u'channels': [channel]}
