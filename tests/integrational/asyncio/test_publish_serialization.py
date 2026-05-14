from datetime import datetime

import pytest

from pubnub.enums import PNStatusCategory
from pubnub.exceptions import PubNubAsyncioException
from pubnub.models.consumer.common import PNStatus
from pubnub.models.consumer.pn_error_data import PNErrorData
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_copy


@pytest.mark.asyncio
async def test_publish_non_serializable_returns_usable_error():
    pubnub = PubNubAsyncio(pnconf_copy())

    result = await pubnub.publish().channel("ch1").message({
        "text": "Hello",
        "timestamp": datetime.now(),
    }).future()

    assert isinstance(result, PubNubAsyncioException)
    assert result.is_error() is True
    assert isinstance(result.status, PNStatus)
    assert result.status.error is True
    assert result.status.category == PNStatusCategory.PNSerializationErrorCategory
    assert isinstance(result.status.error_data, PNErrorData)
    assert str(result) == (
        "Trying to publish not JSON serializable object: "
        "Object of type datetime is not JSON serializable"
    )

    await pubnub.stop()
