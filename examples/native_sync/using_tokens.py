import os
import time
from pubnub.exceptions import PubNubException
from pubnub.models.consumer.v3.channel import Channel
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration

# We are using keyset with Access Manager enabled.
# Admin has superpowers and can grant tokens, access to all channels, etc. Notice admin has secret key.
admin_config = PNConfiguration()
admin_config.publish_key = os.environ.get('PUBLISH_PAM_KEY', 'demo')
admin_config.subscribe_key = os.environ.get('SUBSCRIBE_PAM_KEY', 'demo')
admin_config.secret_key = os.environ.get('SECRET_PAM_KEY', 'demo')
admin_config.uuid = "example_admin"

# User also has the same keyset as admin.
# User has limited access to the channels they are granted access to. Notice user has no secret key.
user_config = PNConfiguration()
user_config.publish_key = os.environ.get('PUBLISH_PAM_KEY', 'demo')
user_config.subscribe_key = os.environ.get('SUBSCRIBE_PAM_KEY', 'demo')
user_config.uuid = "example_user"

admin = PubNub(admin_config)
user = PubNub(user_config)

try:
    user.publish().channel("test_channel").message("test message").sync()
except PubNubException as e:
    print(f"User cannot publish to test_channel as expected.\nError: {e}")

# admin can grant tokens to users
grant_envelope = admin.grant_token() \
    .channels([Channel.id("test_channel").read().write().manage().update().join().delete()]) \
    .authorized_uuid("example_user") \
    .ttl(1) \
    .sync()
assert grant_envelope.status.status_code == 200

token = grant_envelope.result.get_token()
assert token is not None

user.set_token(token)
user.publish().channel("test_channel").message("test message").sync()

# admin can revoke tokens
revoke_envelope = admin.revoke_token(token).sync()
assert revoke_envelope.status.status_code == 200

# We have to wait for the token revoke to propagate.
time.sleep(10)

# user cannot publish to test_channel after token is revoked
try:
    user.publish().channel("test_channel").message("test message").sync()
except PubNubException as e:
    print(f"User cannot publish to test_channel any more.\nError: {e}")
