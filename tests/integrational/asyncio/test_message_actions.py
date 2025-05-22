import unittest

from pubnub.models.consumer.message_actions import PNMessageAction
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_env_copy


class TestMessageActions(unittest.IsolatedAsyncioTestCase):
    pubnub: PubNubAsyncio = None
    channel = "test_message_actions"
    message_timetoken = None

    action_value_1 = "hello"
    action_type_1 = "text"
    action_timetoken_1 = None

    action_value_2 = "👋"
    action_type_2 = "emoji"
    action_timetoken_2 = None

    async def asyncSetUp(self):
        self.pubnub = PubNubAsyncio(pnconf_env_copy())
        # Ensure message is published only once per class, not per test method instance
        if TestMessageActions.message_timetoken is None:
            message_content = "test message for actions"
            result = await self.pubnub.publish().channel(TestMessageActions.channel).message(message_content).future()
            self.assertFalse(result.status.is_error())
            self.assertIsNotNone(result.result.timetoken)
            TestMessageActions.message_timetoken = result.result.timetoken

        self.message_timetoken = TestMessageActions.message_timetoken
        self.assertIsNotNone(self.message_timetoken, "Message timetoken should be set in setUp")

    async def test_01_add_reactions(self):
        # Add first reaction
        add_result_1 = await self.pubnub.add_message_action() \
            .channel(self.channel) \
            .message_action(PNMessageAction().create(
                type=self.action_type_1,
                value=self.action_value_1,
                message_timetoken=self.message_timetoken,
            )) \
            .future()
        self.assertFalse(add_result_1.status.is_error())
        self.assertIsNotNone(add_result_1.result)
        self.assertEqual(add_result_1.result.type, self.action_type_1)
        self.assertEqual(add_result_1.result.value, self.action_value_1)
        self.assertIsNotNone(add_result_1.result.action_timetoken)
        TestMessageActions.action_timetoken_1 = add_result_1.result.action_timetoken

        # Add second reaction
        add_result_2 = await self.pubnub.add_message_action() \
            .channel(self.channel) \
            .message_action(PNMessageAction().create(
                type=self.action_type_2,
                value=self.action_value_2,
                message_timetoken=self.message_timetoken,
            )) \
            .future()
        self.assertFalse(add_result_2.status.is_error())
        self.assertIsNotNone(add_result_2.result)
        self.assertEqual(add_result_2.result.type, self.action_type_2)
        self.assertEqual(add_result_2.result.value, self.action_value_2)
        self.assertIsNotNone(add_result_2.result.action_timetoken)
        TestMessageActions.action_timetoken_2 = add_result_2.result.action_timetoken

    async def test_02_get_added_reactions(self):
        self.assertIsNotNone(TestMessageActions.action_timetoken_1, "Action timetoken 1 not set by previous test")
        self.assertIsNotNone(TestMessageActions.action_timetoken_2, "Action timetoken 2 not set by previous test")

        # Get all reactions
        get_reactions_result = await self.pubnub.get_message_actions() \
            .channel(self.channel) \
            .future()

        self.assertFalse(get_reactions_result.status.is_error())
        self.assertIsNotNone(get_reactions_result.result)
        self.assertEqual(len(get_reactions_result.result.actions), 2)

        # Verify reactions content (order might vary)
        actions = get_reactions_result.result.actions
        found_reaction_1 = False
        found_reaction_2 = False
        for action in actions:
            if action.action_timetoken == TestMessageActions.action_timetoken_1:
                self.assertEqual(action.type, self.action_type_1)
                self.assertEqual(action.value, self.action_value_1)
                self.assertEqual(action.uuid, self.pubnub.config.user_id)
                found_reaction_1 = True
            elif action.action_timetoken == TestMessageActions.action_timetoken_2:
                self.assertEqual(action.type, self.action_type_2)
                self.assertEqual(action.value, self.action_value_2)
                self.assertEqual(action.uuid, self.pubnub.config.user_id)
                found_reaction_2 = True
        self.assertTrue(found_reaction_1, "Added reaction 1 not found in get_message_actions")
        self.assertTrue(found_reaction_2, "Added reaction 2 not found in get_message_actions")

        # Get reactions with limit = 1
        get_reactions_limited_result = await self.pubnub.get_message_actions() \
            .channel(self.channel) \
            .limit('1') \
            .future()
        self.assertFalse(get_reactions_limited_result.status.is_error())
        self.assertIsNotNone(get_reactions_limited_result.result)
        self.assertEqual(len(get_reactions_limited_result.result.actions), 1)

    async def test_03_get_message_history_with_reactions(self):
        fetch_result = await self.pubnub.fetch_messages() \
            .channels(self.channel) \
            .include_message_actions(True) \
            .start(int(TestMessageActions.message_timetoken + 100)) \
            .end(int(TestMessageActions.message_timetoken - 100)) \
            .count(1) \
            .future()
        self.assertIsNotNone(fetch_result.result)
        self.assertIn(self.channel, fetch_result.result.channels)
        messages_in_channel = fetch_result.result.channels[self.channel]
        self.assertEqual(len(messages_in_channel), 1)
        # Ensure reactions were added by previous tests
        self.assertIsNotNone(TestMessageActions.action_timetoken_1, "Dependency: action_timetoken_1 not set")
        self.assertIsNotNone(TestMessageActions.action_timetoken_2, "Dependency: action_timetoken_2 not set")

        message_with_actions = messages_in_channel[0]
        self.assertEqual(int(message_with_actions.timetoken), TestMessageActions.message_timetoken)
        self.assertTrue(hasattr(message_with_actions, 'actions'))
        self.assertIsNotNone(message_with_actions.actions)

        total_actions_in_history = 0
        if message_with_actions.actions:
            for reaction_type_key in message_with_actions.actions:
                for reaction_value_key in message_with_actions.actions[reaction_type_key]:
                    action_list = message_with_actions.actions[reaction_type_key][reaction_value_key]
                    total_actions_in_history += len(action_list)

        self.assertEqual(total_actions_in_history, 2)

        actions_dict = message_with_actions.actions
        self.assertIn(self.action_type_1, actions_dict)
        self.assertIn(self.action_value_1, actions_dict[self.action_type_1])
        action1_list = actions_dict[self.action_type_1][self.action_value_1]
        self.assertEqual(len(action1_list), 1)
        self.assertEqual(action1_list[0]['uuid'], self.pubnub.config.user_id)
        self.assertEqual(action1_list[0]['actionTimetoken'], TestMessageActions.action_timetoken_1)

        self.assertIn(self.action_type_2, actions_dict)
        self.assertIn(self.action_value_2, actions_dict[self.action_type_2])
        action2_list = actions_dict[self.action_type_2][self.action_value_2]
        self.assertEqual(len(action2_list), 1)
        self.assertEqual(action2_list[0]['uuid'], self.pubnub.config.user_id)
        self.assertEqual(action2_list[0]['actionTimetoken'], TestMessageActions.action_timetoken_2)

    async def test_04_remove_reactions(self):
        # Ensure reactions were added by previous tests
        self.assertIsNotNone(TestMessageActions.action_timetoken_1, "Dependency: action_timetoken_1 not set")
        self.assertIsNotNone(TestMessageActions.action_timetoken_2, "Dependency: action_timetoken_2 not set")

        # Get all reactions to prepare for removal (specific ones added in this test class)
        action_tt_to_remove_1 = TestMessageActions.action_timetoken_1
        action_tt_to_remove_2 = TestMessageActions.action_timetoken_2

        # Remove first reaction
        remove_result_1 = await self.pubnub.remove_message_action() \
            .channel(self.channel) \
            .message_timetoken(TestMessageActions.message_timetoken) \
            .action_timetoken(action_tt_to_remove_1) \
            .future()
        self.assertFalse(remove_result_1.status.is_error())
        self.assertIsNotNone(remove_result_1.result)
        self.assertEqual(remove_result_1.result, {})

        # Remove second reaction
        remove_result_2 = await self.pubnub.remove_message_action() \
            .channel(self.channel) \
            .message_timetoken(TestMessageActions.message_timetoken) \
            .action_timetoken(action_tt_to_remove_2) \
            .future()
        self.assertFalse(remove_result_2.status.is_error())
        self.assertIsNotNone(remove_result_2.result)
        self.assertEqual(remove_result_2.result, {})

        # Verify these specific reactions were removed
        get_reactions_after_removal_result = await self.pubnub.get_message_actions() \
            .channel(self.channel) \
            .future()

        self.assertFalse(get_reactions_after_removal_result.status.is_error())
        self.assertIsNotNone(get_reactions_after_removal_result.result)
        self.assertEqual(len(get_reactions_after_removal_result.result.actions), 0)

    async def test_05_remove_all_reactions(self):
        envelope = await self.pubnub.get_message_actions() \
            .channel(self.channel) \
            .limit("100") \
            .future()

        for action in envelope.result.actions:
            remove_result = await self.pubnub.remove_message_action() \
                .channel(self.channel) \
                .message_timetoken(action.message_timetoken) \
                .action_timetoken(action.action_timetoken) \
                .future()
            self.assertFalse(remove_result.status.is_error())
            self.assertIsNotNone(remove_result.result)
            self.assertEqual(remove_result.result, {})

        envelope = await self.pubnub.get_message_actions() \
            .channel(self.channel) \
            .limit("100") \
            .future()
        self.assertFalse(envelope.status.is_error())
        self.assertIsNotNone(envelope.result)
        self.assertEqual(len(envelope.result.actions), 0)

    async def asyncTearDown(self):
        if self.pubnub:
            await self.pubnub.stop()
