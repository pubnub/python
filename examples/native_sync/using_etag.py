import os

from copy import deepcopy
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.exceptions import PubNubException

config = PNConfiguration()
config.publish_key = os.getenv('PUBLISH_KEY', default='demo')
config.subscribe_key = os.getenv('SUBSCRIBE_KEY', default='demo')
config.user_id = "example"

config_2 = deepcopy(config)
config_2.user_id = "example_2"

pubnub = PubNub(config)
pubnub_2 = PubNub(config_2)

sample_user = {
    "uuid": "SampleUser",
    "name": "John Doe",
    "email": "jd@example.com",
    "custom": {"age": 42, "address": "123 Main St."},
}

# One client creates a metada for the user "SampleUser" and successfully writes it to the server.
set_result = pubnub.set_uuid_metadata(
    **sample_user,
    include_custom=True,
    include_status=True,
    include_type=True
).sync()

# We store the eTag for the user for further updates.
e_tag = set_result.result.data.get('eTag')

# Another client sets the user meta with the same UUID but different data.
overwrite_result = pubnub_2.set_uuid_metadata(uuid="SampleUser", name="Jane Doe").sync()
new_e_tag = overwrite_result.result.data.get('eTag')

# We can verify that there is a new eTag for the user.
print(f"{e_tag == new_e_tag=}")

# We modify the user and try to update it.
updated_user = {**sample_user, "custom": {"age": 43, "address": "321 Other St."}}

try:
    update_result = pubnub.set_uuid_metadata(
        **updated_user,
        include_custom=True,
        include_status=True,
        include_type=True
    ).if_matches_etag(e_tag).sync()
except PubNubException as e:
    # We get an exception and after reading the error message we can see that the reason is that the eTag is outdated.
    print(f"Update failed: {e.get_error_message().get('message')}")

