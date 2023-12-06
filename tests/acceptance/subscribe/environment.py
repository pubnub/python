import requests

from behave.runner import Context
from io import StringIO
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
    context.pubnub.unsubscribe_all()
    for tag in feature.tags:
        if "contract" in tag:
            response = requests.get(MOCK_SERVER_URL + CONTRACT_EXPECT_ENDPOINT)
            assert response

            response_json = response.json()

            assert not response_json["expectations"]["failed"]
            assert not response_json["expectations"]["pending"]
