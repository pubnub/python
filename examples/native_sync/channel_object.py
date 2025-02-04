from pprint import pprint
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration

config = PNConfiguration()
config.publish_key = 'demo'
config.subscribe_key = 'demo'
config.user_id = 'example'

channel = "demo_example"
help_string = "\tTo exit type '/exit'\n\tTo show the current object type '/show'\n\tTo show this help type '/help'\n"

pubnub = PubNub(config)

print(f"We're setting the channel's {channel} additional info. \n{help_string}\n")

name = input("Enter the channel name: ")
description = input("Enter the channel description: ")

# Setting the basic channel info
set_result = pubnub.set_channel_metadata(
    channel,
    name=name,
    description=description,
).sync()
print("The channel has been created with name and description.\n")

# We start to iterate over the custom fields
while True:
    # First we have to get the current object to know what fields are already set
    current_object = pubnub.get_channel_metadata(
        channel,
        include_custom=True,
        include_status=True,
        include_type=True
    ).sync()

    # Gathering new data
    field_name = input("Enter the field name: ")
    if field_name == '/exit':
        break
    if field_name == '/show':
        pprint(current_object.result.data, indent=2)
        print()
        continue
    if field_name == '/help':
        print(help_string, end="\n\n")
        continue

    field_value = input("Enter the field value: ")

    # We may have to initialize the custom field
    custom = current_object.result.data.get('custom', {})
    if custom is None:
        custom = {}

    # We have to check if the field already exists and
    if custom.get(field_name):
        confirm = input(f"Field {field_name} already has a value. Overwrite? (y/n):").lower()
        while confirm not in ['y', 'n']:
            confirm = input("Please enter 'y' or 'n': ").lower()
        if confirm == 'n':
            print("Object will not be updated.\n")
            continue
        if confirm == 'y':
            custom[field_name] = field_value
    else:
        custom[field_name] = field_value

    # Writing the updated object back to the server
    set_result = pubnub.set_channel_metadata(
        channel,
        custom=custom,
        name=current_object.result.data.get('name'),
        description=current_object.result.data.get('description')
    ).sync()
    print("Object has been updated.\n")
