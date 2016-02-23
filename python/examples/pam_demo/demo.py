from gevent.monkey import patch_all
from pubnub import Pubnub
import random
import json

patch_all()

rand = str(random.randint(1, 99999999))


def get_unique(s):
    return 'str-' + rand + '-' + s


# public channel
# This is the channel all clients announce themselves on -- or more generally speaking, a channel you expect the client
# to "check-in" on to announce his state

# channel_public = get_unique("channel_public")
channel_public = "channel_public"

# server auth key
# Only the server has/knows about this auth token. It will be used to grant read on the "check-in" Presence channel

# server_auth_token = get_unique("server_auth_token")
server_auth_token = "server_auth_token"

# client auth key
# only clients will use this authey -- it does not provide presence channel read access

# client_auth_token = get_unique("client_auth_token")
client_auth_token = "client_auth_token"

# each client must have a unique id -- a UUID, for presence information/state to bind to

# client uuid
client_uuid = get_unique("client_uuid")

# server uuid
server_uuid = get_unique("server_uuid")

# For the demo, we'll implement a SERVER called server, who is the authoritative 'admin' entity in the system
# We'll also implement a CLIENT called client, who is an arbitrary hardware device member of the network

# Please swap out the default 'pam' demo keys with your own PAM-enabled keys

# init server object
server = Pubnub(publish_key="pam", subscribe_key="pam", secret_key="pam", auth_key=server_auth_token, uuid=server_uuid)

# init client object
client = Pubnub(publish_key="pam", subscribe_key="pam", auth_key=client_auth_token, uuid=client_uuid)

# To access a Presence channel with PAM, its format is CHANNELNAME-pnpres

# Grant permission to server auth keys
# grant r/w to public, and r/w public Presence (public-pnpres)

print(server.grant(channel=channel_public, auth_key=server_auth_token, read=True, write=True))
print(server.grant(channel=channel_public + '-pnpres', auth_key=server_auth_token, read=True, write=True))

# Grant permission to client auth keys
# grant r/w to public, and w-only access to public Presence (public-pnpres)
print(server.grant(channel=channel_public, auth_key=client_auth_token, read=True, write=False))
print(server.grant(channel=channel_public + '-pnpres', auth_key=client_auth_token, read=False, write=False))


# Now, we'll run it to watch it work as advertised...

# Define some simple callabcks for the Server and Client

def _server_message_callback(message, channel):
    print("Server heard: " + json.dumps(message))


def _client_message_callback(message, channel):
    print("Client heard: " + json.dumps(message))


def _client_error_callback(error, channel):
    print("Client Error: " + error + " on channel " + channel)
    print("TTL on grant expired, or token was invalid, or revoked."
          " Client will now unsubscribe from this unauthorized channel.")
    client.unsubscribe(channel=channel)


def _server_error_callback(error, channel):
    print("Server Error: " + error + " on channel " + channel)
    print("TTL on grant expired, or token was revoked. Server will now unsubscribe from this unauthorized channel.")
    server.unsubscribe(channel=channel)


def _server_presence_callback(message, channel):
    print(message)
    if 'action' in message:
        if message['action'] == 'join' and message['uuid'] == client_uuid:
            print("Server can see that client with UUID " + message['uuid'] + " has a state of " + json.dumps(
                message['data']))


def _client_presence_callback(message, channel):
    print(message)
    if 'action' in message:
        if message['action'] == 'join' and message['uuid'] == client_uuid:
            print("Client can see that client with UUID " + message['uuid'] + " has a state of " + json.dumps(
                message['data']))


# server subscribes to public channel
server.subscribe(channels=channel_public, callback=_server_message_callback, error=_server_error_callback)

# server subscribes to presence events on public channel
# presence() is a convienence method that subscribes to channel-pnpres with special logic for handling
# presence-event formatted messages

# uncomment out to see server able to read on presence channel
server.presence(channel=channel_public, callback=_server_presence_callback, error=_server_error_callback)

# now if the client tried to subscribe on the presence channel, and therefore, get state info
# he is explicitly denied!

# uncomment out to see client not able to read on presence channel
client.presence(channel=channel_public, callback=_client_presence_callback, error=_client_error_callback)

# client subscribes to public channel
client.subscribe(channels=channel_public, state={"myKey": get_unique("foo")}, callback=_client_message_callback,
                 error=_client_error_callback)
