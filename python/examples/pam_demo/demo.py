
from gevent.monkey import patch_all
patch_all()

import sys
from Pubnub import Pubnub
import random
import json

rand = str(random.randint(1,99999999))

def get_unique(s):
	return 'str-' + rand + '-' + s

# public channel
channel_public = get_unique("channel_public")

# server auth key
server_auth_token = get_unique("server_auth_token")

#client auth key
client_auth_token = get_unique("client_auth_token")

#client uuid
client_uuid = get_unique("client_uuid")

#server uuid
server_uuid = get_unique("server_uuid")


#init server object
server = Pubnub(publish_key="pam", subscribe_key="pam", secret_key="pam", auth_key=server_auth_token, uuid=server_uuid)

#init client object
client = Pubnub(publish_key="pam", subscribe_key="pam", auth_key=client_auth_token, uuid=client_uuid)

# Grant permission to server auth keys
print(server.grant(channel=channel_public, auth_key=server_auth_token, read=True, write=True))
print(server.grant(channel=channel_public + '-pnpres', auth_key=server_auth_token, read=True, write=True))

# Grant permission to client auth keys
print(server.grant(channel=channel_public, auth_key=client_auth_token, read=True, write=False))
print(server.grant(channel=channel_public + '-pnpres', auth_key=client_auth_token, read=True, write=False))



def _server_callback(message, channel):
	print(message)

def _error_callback(error):
	print(error)

#server subscribes to public channel
server.subscribe(channels=channel_public, callback=_server_callback, error=_error_callback)



def _server_presence_callback(message, channel):
	print message
	if 'action' in message:
		if message['action'] == 'join' and message['uuid'] == client_uuid:
			print "Only I can see that client with UUID " + message['uuid'] + " has a state of " + json.dumps(message['data'])

# server subscribes to presence events on public channel 
server.presence(channel=channel_public, callback=_server_presence_callback, error=_error_callback)




def _client_callback(channel, message):
	print(message)

# client subscribes to public channel
client.subscribe(channels=channel_public, state={ "myKey" : get_unique("foo")}, callback=_client_callback, error=_error_callback)
