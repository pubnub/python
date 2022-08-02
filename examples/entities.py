import os

from pubnub.models.consumer.entities.space import Space
from pubnub.models.consumer.entities.user import User
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub

pnconfig = PNConfiguration()

pnconfig.subscribe_key = os.getenv('SUB_KEY')
pnconfig.publish_key = os.getenv('PUB_KEY')
pnconfig.secret_key = os.getenv('SEC_KEY')
pnconfig.user_id = "my_uuid"

pnconfig.non_subscribe_request_timeout = 60
pnconfig.connect_timeout = 14
pnconfig.reconnect_policy

pubnub = PubNub(pnconfig)

space_id = 'blah'
user_id = 'jason-id'
user_id_2 = 'freddy-id'

create_space = pubnub.create_space(
    space_id=space_id,
    name=f'Space ID {space_id}',
    description=f'This space ID is {space_id} and is made for demo purpose only',
    custom={"created_by": "me"},
    space_status='Primary',
    space_type='COM',
    sync=True
)

print(f"create space result:{create_space.result.__dict__}")

update_space = pubnub.update_space(
    space_id=space_id,
    name=f'EDIT Space ID {space_id}',
    description=f'EDIT: This space ID is {space_id} and is made for demo purpose only',
    custom={"created_by": "EDIT me"},
    sync=True
)
print(f"update space result: {update_space.result.__dict__}")

fetch_space = pubnub.fetch_space(space_id=space_id, include_custom=True, sync=True)
print(f"fetch space result: {fetch_space.result.__dict__}")

space_id2 = space_id + '2'
create_space = pubnub.create_space(space_id2) \
    .set_name(f'Space ID {space_id}') \
    .description(f'This space ID is {space_id} and is made for demo purpose only') \
    .custom({
        "created_by": "me"
    }) \
    .sync()

all_spaces = pubnub.fetch_spaces(include_custom=True, include_total_count=True).sync()

print(f"fetch spaces result: {all_spaces.result.__dict__}")

rm_space = pubnub.remove_space(space_id2).sync()
print(f"remove space result: {rm_space.result.__dict__}")

user = pubnub.create_user(user_id=user_id, name='Jason', email='Jason@Voorhe.es', sync=True)

users = pubnub.fetch_user(user_id=user_id, sync=True)
print(f"fetch_user: {users.result.__dict__}")

membership = pubnub.add_memberships(user_id=user_id, spaces=[Space(space_id=space_id, custom={"a": "b"})], sync=True)
print(f"add_memberships (user_id): {membership.result.__dict__}")

memberships = pubnub.fetch_memberships(user_id=user_id, include_custom=True, sync=True)
print(f"fetch_memberships (user_id): {memberships.result.__dict__}")

print("-------")

membership = pubnub.update_memberships(user_id=user_id, spaces=[Space(space_id=space_id, custom={"c": "d"})], sync=True)
print(f"add_memberships (user_id): {membership.result.__dict__}")

memberships = pubnub.fetch_memberships(user_id=user_id, include_custom=True, sync=True)
print(f"fetch_memberships (user_id): {memberships.result.__dict__}")

print("-------")

membership = pubnub.add_memberships(
    user_id=user_id, spaces=[Space(space_id='some_2nd_space_id'), Space(space_id='some_3rd_space_id')], sync=True
)
print(f"add_memberships (user_id): {membership.result.__dict__}")

memberships = pubnub.fetch_memberships(user_id=user_id, include_custom=True, sync=True)
print(f"fetch_memberships (user_id): {memberships.result.__dict__}")

print("-------")

membership = pubnub.remove_memberships(user_id=user_id, spaces=[Space(space_id=space_id)], sync=True)
print(f"remove_memberships (user_id): {membership.result.__dict__}")

memberships = pubnub.fetch_memberships(user_id=user_id, include_custom=True, sync=True)
print(f"fetch_memberships (user_id): {memberships.result.__dict__}")

print("-------")

membership = pubnub.add_memberships(
    space_id=space_id,
    users=[User(user_id=user_id, custom={"Kikiki": "Mamama"})],
    sync=True
)
print(f"add_memberships (space_id): {membership.result.__dict__}")

membership = pubnub.update_memberships(space_id=space_id, users=[
    User(user_id=user_id_2, custom={"1-2": "Freddy's comming"}),
    User(user_id='ghostface', custom={"question": "Favourite scary movie?"})
], sync=True)
print(f"update_memberships (space_id): {membership.result.__dict__}")

print("-------")

memberships = pubnub.fetch_memberships(space_id=space_id, include_custom=True, sync=True)
print(f"fetch_memberships (space_id): {memberships.result.__dict__}")
