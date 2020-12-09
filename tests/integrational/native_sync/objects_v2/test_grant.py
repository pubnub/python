import unittest

from pubnub.models.consumer.access_manager import PNAccessManagerGrantResult, PNAccessManagerKeyData
from pubnub.models.consumer.common import PNStatus
from pubnub.pubnub import PubNub
from pubnub.structures import Envelope
from tests.helper import pnconf_copy
from tests.integrational.vcr_helper import pn_vcr


def _pubnub_admin():
    config = pnconf_copy()
    config.subscribe_key = "SUB_KEY"
    config.secret_key = "SECRET_KEY"
    return PubNub(config)


class TestGrantObjV2(unittest.TestCase):
    _some_uuid = "someuuid"

    @pn_vcr.use_cassette('tests/integrational/fixtures/native_sync/objects_v2/pam/grant.yaml',
                         filter_query_parameters=['uuid', 'pnsdk', 'timestamp', 'signature'])
    def test_grant(self):
        pn = _pubnub_admin()
        auth_key = "authKey123"

        grant_result = pn.grant() \
            .uuids([self._some_uuid]) \
            .auth_keys([auth_key]) \
            .ttl(120).get(True) \
            .update(True) \
            .join(True) \
            .sync()

        assert isinstance(grant_result, Envelope)
        assert isinstance(grant_result.status, PNStatus)
        assert isinstance(grant_result.result, PNAccessManagerGrantResult)
        assert grant_result.result.uuids[self._some_uuid] is not None
        assert grant_result.result.uuids[self._some_uuid] is not None
        assert grant_result.result.uuids[self._some_uuid].auth_keys[auth_key] is not None
        assert isinstance(grant_result.result.uuids[self._some_uuid].auth_keys[auth_key], PNAccessManagerKeyData)
        assert grant_result.result.uuids[self._some_uuid].auth_keys[auth_key].get is True
        assert grant_result.result.uuids[self._some_uuid].auth_keys[auth_key].update is True
        assert grant_result.result.uuids[self._some_uuid].auth_keys[auth_key].join is True
