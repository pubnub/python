import os

from pubnub.models.consumer.entities.user import User
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

config = PNConfiguration()
config.subscribe_key = os.getenv('PN_KEY_SUBSCRIBE')
config.publish_key = os.getenv('PN_KEY_PUBLISH')
config.user_id = 'example'

pubnub = PubNub(config)

pubnub.set_uuid_metadata().uuid('john').set_name('John Lorem').sync()
pubnub.set_uuid_metadata().uuid('jim').set_name('Jim Ipsum').sync()

john_metadata = pubnub.get_all_uuid_metadata().filter("name LIKE 'John*'").sync()

if john_metadata.status.is_error():
    print(f"Error fetching UUID metadata: {john_metadata.status.error_message}")
else:
    for uuid_data in john_metadata.result.data:
        print(f"UUID: {uuid_data['id']}, Name: {uuid_data['name']}")

pubnub.set_channel_metadata().channel('generalfailure').set_name('General Failure').sync()
pubnub.set_channel_metadata().channel('majormistake').set_name('Major Mistake').sync()

general_metadata = pubnub.get_all_channel_metadata() \
    .filter("name LIKE '*general*' && updated >= '2023-01-01T00:00:00Z'") \
    .sync()

if general_metadata.status.is_error():
    print(f"Error fetching channel metadata: {general_metadata.status.__dict__}")
else:
    for channel in general_metadata.result.data:
        print(f"Channel ID: {channel['id']}, Name: {channel['name']}, Updated: {channel['updated']}")

pubnub.set_channel_members().channel('example').uuids([User('user123'), User('user124')]).sync()

memberships = pubnub.get_memberships() \
    .uuid("user123") \
    .filter("!(channel.id == 'Channel-001')") \
    .sync()

if memberships.status.is_error():
    print(f"Error fetching memberships: {memberships.status}")
else:
    print(memberships.__dict__)
    for membership in memberships.result.data:
        print(f"Channel ID: {membership['channel']['id']}")


members = pubnub.get_channel_members() \
    .channel("specialEvents") \
    .filter("uuid.updated < '2023-01-01T00:00:00Z'") \
    .sync()

print(members.result)
