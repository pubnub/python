import os
from typing import Dict, Any
from pubnub.models.consumer.message_actions import PNMessageAction
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub


# snippet.init_pubnub
def initialize_pubnub(
    publish_key: str,
    subscribe_key: str,
    user_id: str
) -> PubNub:
    """
    Initialize a PubNub instance with the provided configuration.

    Args:
        publish_key (str): PubNub publish key
        subscribe_key (str): PubNub subscribe key
        user_id (str): User identifier for PubNub

    Returns:
        PubNub: Configured PubNub instance ready for publishing and subscribing
    """
    pnconfig = PNConfiguration()

    # Configure keys with provided values
    pnconfig.publish_key = publish_key
    pnconfig.subscribe_key = subscribe_key
    pnconfig.user_id = user_id

    return PubNub(pnconfig)
# snippet.end


# snippet.publish_message
def publish_message(pubnub: PubNub, channel: str, message: Any) -> Dict:
    """
    Publish a message to a specific channel.

    Args:
        pubnub (PubNub): PubNub instance
        channel (str): Channel to publish to
        message (Any): Message content to publish

    Returns:
        Dict: Publish operation result containing timetoken
    """
    envelope = pubnub.publish().channel(channel).message(message).sync()
    return envelope.result
# snippet.end


# snippet.publish_reaction
def publish_reaction(
    pubnub: PubNub,
    channel: str,
    message_timetoken: str,
    reaction_type: str,
    reaction_value: str,
    user_id: str

) -> Dict:
    """
    Publish a reaction to a specific message.

    Args:
        pubnub (PubNub): PubNub instance
        channel (str): Channel where the original message was published
        message_timetoken (str): Timetoken of the message to react to
        reaction_type (str): Type of reaction (e.g. "smile", "thumbs_up")

    Returns:
        Dict: Reaction publish operation result
    """
    message_action = PNMessageAction().create(
        type=reaction_type,
        value=reaction_value,
        message_timetoken=message_timetoken,
        user_id=user_id
    )
    envelope = pubnub.add_message_action().channel(channel).message_action(message_action).sync()

    return envelope.result
# snippet.end


# snippet.get_reactions
def get_reactions(pubnub: PubNub, channel: str, start_timetoken: str, end_timetoken: str, limit: str) -> Dict:
    """
    Get reactions for a specific message.

    Args:
        pubnub (PubNub): PubNub instance
        channel (str): Channel where the original message was published
        start_timetoken (str): Start timetoken of the message to get reactions for
        end_timetoken (str): End timetoken of the message to get reactions for
        limit (str): Limit the number of reactions to return
    Returns:
        Dict: Reactions for the message
    """
    envelope = pubnub.get_message_actions() \
        .channel(channel) \
        .start(start_timetoken) \
        .end(end_timetoken) \
        .limit(limit) \
        .sync()
    return envelope.result
# snippet.end


# snippet.remove_reaction
def remove_reaction(pubnub: PubNub, channel: str, message_timetoken: str, action_timetoken: str) -> Dict:
    """
    Remove a reaction from a specific message.

    Args:
        pubnub (PubNub): PubNub instance
        channel (str): Channel where the original message was published
        message_timetoken (str): Timetoken of the message to react to
        action_timetoken (str): Timetoken of the reaction to remove
    """
    envelope = pubnub.remove_message_action() \
        .channel(channel) \
        .message_timetoken(message_timetoken) \
        .action_timetoken(action_timetoken) \
        .sync()
    return envelope.result
# snippet.end


def main() -> None:
    """
    Main execution function.
    """
    # Get configuration from environment variables or use defaults
    publish_key = os.getenv('PUBLISH_KEY', 'demo')
    subscribe_key = os.getenv('SUBSCRIBE_KEY', 'demo')
    user_id = os.getenv('USER_ID', 'example-user')

    # snippet.usage_example
    # Initialize PubNub instance with configuration
    # If environment variables are not set, demo keys will be used
    pubnub = initialize_pubnub(
        publish_key=publish_key,
        subscribe_key=subscribe_key,
        user_id=user_id
    )

    # Channel where all the communication will happen
    channel = "my_channel"

    # Message that will receive reactions
    message = "Hello, PubNub!"

    # Step 1: Publish initial message
    # The timetoken is needed to add reactions to this specific message
    result = publish_message(pubnub, channel, message)
    message_timetoken = result.timetoken
    assert result.timetoken is not None, "Message publish failed - no timetoken returned"
    assert isinstance(result.timetoken, (int, str)) and str(result.timetoken).isnumeric(), "Invalid timetoken format"
    print(f"Published message with timetoken: {result.timetoken}")

    # Step 2: Add different types of reactions from different users
    # First reaction: text-based reaction from guest_1
    reaction_type = "text"
    reaction_value = "Hello"
    first_reaction = publish_reaction(pubnub, channel, message_timetoken, reaction_type, reaction_value, "guest_1")
    print(f"Added first reaction {first_reaction.__dict__}")
    assert first_reaction is not None, "Reaction publish failed - no result returned"
    assert isinstance(first_reaction, PNMessageAction), "Invalid reaction result type"

    # Second reaction: emoji-based reaction from guest_2
    reaction_type = "emoji"
    reaction_value = "👋"
    second_reaction = publish_reaction(pubnub, channel, message_timetoken, reaction_type, reaction_value, "guest_2")
    print(f"Added second reaction {second_reaction.__dict__}")
    assert second_reaction is not None, "Reaction publish failed - no result returned"
    assert isinstance(second_reaction, PNMessageAction), "Invalid reaction result type"

    # Step 3: Fetch the message with its reactions from history
    fetch_result = pubnub.fetch_messages()\
        .channels(channel)\
        .include_message_actions(True)\
        .count(1)\
        .sync()

    messages = fetch_result.result.channels[channel]
    print(f"Fetched message with reactions: {messages[0].__dict__}")
    assert len(messages) == 1, "Message not found in history"
    assert hasattr(messages[0], 'actions'), "Message actions not included in response"
    assert len(messages[0].actions) >= 2, "Unexpected number of actions in history"

    # Step 4: Retrieve all reactions for the message
    # We use a time window around the message timetoken to fetch reactions
    # The window is 1000 time units before and after the message
    start_timetoken = str(int(message_timetoken) - 1000)
    end_timetoken = str(int(message_timetoken) + 1000)
    reactions = get_reactions(pubnub, channel, start_timetoken, end_timetoken, "100")
    print(f"Reactions found: {len(reactions.actions)}")
    assert len(reactions.actions) >= 2, "Unexpected number of reactions"

    # Step 5: Display and remove each reaction
    for reaction in reactions.actions:
        print(f"    Reaction: {reaction.__dict__}")
        # Remove the reaction and confirm removal
        remove_reaction(pubnub, channel, reaction.message_timetoken, reaction.action_timetoken)
        print(f"Removed reaction {reaction.__dict__}")

    # Step 6: Verify reactions were removed
    # Fetch reactions again - should be empty now
    reactions = get_reactions(pubnub, channel, start_timetoken, end_timetoken, "100")
    print(f"Reactions found: {len(reactions.actions)}")
    assert len(reactions.actions) == 0, "Unexpected number of reactions"
    # snippet.end


if __name__ == '__main__':
    main()
