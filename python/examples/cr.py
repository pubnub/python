## www.pubnub.com - PubNub Real-time push service in the cloud.
# coding=utf8

## PubNub Real-time Push APIs and Notifications Framework
## Copyright (c) 2010 Stephen Blum
## http://www.pubnub.com/


import sys
from Pubnub import Pubnub

publish_key = len(sys.argv) > 1 and sys.argv[1] or 'pam'
subscribe_key = len(sys.argv) > 2 and sys.argv[2] or 'pam'
secret_key = len(sys.argv) > 3 and sys.argv[3] or 'pam'
cipher_key = len(sys.argv) > 4 and sys.argv[4] or ''
ssl_on = len(sys.argv) > 5 and bool(sys.argv[5]) or False

## -----------------------------------------------------------------------
## Initiate Pubnub State
## -----------------------------------------------------------------------
pubnub = Pubnub(publish_key=publish_key, subscribe_key=subscribe_key,
                secret_key=secret_key, cipher_key=cipher_key, ssl_on=ssl_on, auth_key="abcd")
channel = 'hello_world'

def callback(message):
    print(message)

print pubnub.revoke(channel_group='dev:abcd', auth_key="abcd")
print pubnub.audit(channel_group="dev:abcd")
print pubnub.grant(channel_group='dev:abcd', read=True, write=True, manage=True, auth_key="abcd")
print pubnub.channel_group_list_namespaces()
print pubnub.channel_group_list_groups(namespace='aaa')
print pubnub.channel_group_list_groups(namespace='foo')
print pubnub.channel_group_list_channels(channel_group='dev:abcd')
print pubnub.channel_group_add_channel(channel_group='dev:abcd', channel="hi")
print pubnub.channel_group_list_channels(channel_group='dev:abcd')
print pubnub.channel_group_remove_channel(channel_group='dev:abcd', channel="hi")
print pubnub.channel_group_list_channels(channel_group='dev:abcd')


pubnub.revoke(channel_group='dev:abcd', auth_key="abcd", callback=callback, error=callback)
pubnub.audit(channel_group="dev:abcd", callback=callback, error=callback)
pubnub.grant(channel_group='dev:abcd', read=True, write=True, manage=True, auth_key="abcd", callback=callback, error=callback)
pubnub.channel_group_list_namespaces(callback=callback, error=callback)
pubnub.channel_group_list_groups(namespace='aaa', callback=callback, error=callback)
pubnub.channel_group_list_groups(namespace='foo', callback=callback, error=callback)
pubnub.channel_group_list_channels(channel_group='dev:abcd', callback=callback, error=callback)
pubnub.channel_group_add_channel(channel_group='dev:abcd', channel="hi", callback=callback, error=callback)
pubnub.channel_group_list_channels(channel_group='dev:abcd', callback=callback, error=callback)
pubnub.channel_group_remove_channel(channel_group='dev:abcd', channel="hi", callback=callback, error=callback)
pubnub.channel_group_list_channels(channel_group='dev:abcd', callback=callback, error=callback)
