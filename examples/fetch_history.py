from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


# Fetch historical messages
def fetch_history(pubnub: PubNub, channel_name: str, fetch_count: int):
    envelope = pubnub.history() \
        .channel(channel_name) \
        .include_meta(True) \
        .reverse(False) \
        .include_timetoken(True) \
        .count(fetch_count) \
        .sync()

    # Process and print messages
    if envelope.status.is_error():
        print("Error fetching history:", envelope.status.error_data.information)
    else:
        for message in envelope.result.messages:
            print(f"Message: {message.entry}, Timetoken: {message.timetoken}")


def populate_messages(pubnub: PubNub, channel_name: str, message_count: int):
    for i in range(message_count):
        pubnub.publish().channel(channel_name).message(f'demo message #{i + 1}').sync()


def get_input_number(message: str, range_min: int, range_max: int):
    while True:
        try:
            num = int(input(f"{message} [{range_min}-{range_max}]: "))
            if range_min <= range_max <= 150:
                return num
            else:
                print(f"Invalid input. Please enter a number between {range_min} and {range_max}.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")


if __name__ == "__main__":
    message_count = 0
    channel_name = 'example_fetch_history'

    # Initialize PubNub configuration
    pnconfig = PNConfiguration()
    pnconfig.subscribe_key = "demo"
    pnconfig.publish_key = "demo"
    pnconfig.user_id = "demo"

    # Initialize PubNub
    pubnub = PubNub(pnconfig)

    # Get validated int input between 0 and 150
    message_count = get_input_number("How many messages to populate?", 0, 150)

    populate_messages(pubnub, channel_name, message_count)

    fetch_count = get_input_number("How many messages to fetch?", 0, 100)

    # Call the function to fetch and print history
    fetch_history(pubnub, channel_name, fetch_count)
