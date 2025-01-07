import asyncio
import requests
import logging

from behave.runner import Context
from io import StringIO
from httpx import HTTPError
from pubnub.pubnub import PubNub
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub_asyncio import SubscribeCallback
from tests.acceptance import MOCK_SERVER_URL, CONTRACT_INIT_ENDPOINT, CONTRACT_EXPECT_ENDPOINT


class AcceptanceCallback(SubscribeCallback):
    message_result = None
    status_result = None
    presence_result = None

    def status(self, pubnub, status):
        self.status_result = status

    def message(self, pubnub, message):
        self.message_result = message

    def presence(self, pubnub, presence):
        self.presence_result = presence


class PNContext(Context):
    callback: AcceptanceCallback
    pubnub: PubNub
    pn_config: PNConfiguration
    log_stream: StringIO
    subscribe_response: any


def before_scenario(context: Context, feature):
    for tag in feature.tags:
        if "contract" in tag:
            _, contract_name = tag.split("=")
            response = requests.get(MOCK_SERVER_URL + CONTRACT_INIT_ENDPOINT + contract_name)
            assert response


def after_scenario(context: Context, feature):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(context.pubnub.stop())
    # asyncio cleaning all pending tasks to eliminate any potential state changes
    pending_tasks = asyncio.all_tasks(loop)
    for task in pending_tasks:
        task.cancel()
        try:
            loop.run_until_complete(task)
        except asyncio.CancelledError:
            pass
        except HTTPError as e:
            logger = logging.getLogger("pubnub")
            logger.error(f"HTTPError: {e}")

    loop.run_until_complete(asyncio.sleep(1.5))
    del context.pubnub

    for tag in feature.tags:
        if "contract" in tag:
            response = requests.get(MOCK_SERVER_URL + CONTRACT_EXPECT_ENDPOINT)
            assert response

            response_json = response.json()

            assert not response_json["expectations"]["failed"], str(response_json["expectations"]["failed"])
            assert not response_json["expectations"]["pending"], str(response_json["expectations"]["pending"])
