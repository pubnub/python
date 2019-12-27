import unittest

from pubnub import utils
from pubnub.endpoints.access.audit import Audit
from pubnub.enums import HttpMethod
from pubnub.managers import TelemetryManager

try:
    from mock import MagicMock
except ImportError:
    from unittest.mock import MagicMock

from pubnub.pubnub import PubNub
from tests.helper import pnconf_pam, sdk_name


class TestAudit(unittest.TestCase):
    def setUp(self):
        self.pubnub = MagicMock(
            spec=PubNub,
            config=pnconf_pam,
            sdk_name=sdk_name,
            timestamp=MagicMock(return_value=123),
            uuid=None
        )
        self.pubnub.uuid = "UUID_AuditUnitTest"
        self.pubnub._telemetry_manager = TelemetryManager()
        self.audit = Audit(self.pubnub)

    def test_audit_channel(self):
        self.audit.channels('ch')

        self.assertEqual(self.audit.build_path(), Audit.AUDIT_PATH % pnconf_pam.subscribe_key)

        pam_args = utils.prepare_pam_arguments({
            'timestamp': 123,
            'channel': 'ch',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })

        sign_input = HttpMethod.string(self.audit.http_method()).upper() + "\n" + \
            pnconf_pam.publish_key + "\n" + \
            self.audit.build_path() + "\n" + \
            pam_args + "\n"

        self.assertEqual(self.audit.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'timestamp': '123',
            'channel': 'ch',
            'signature': "v2." + utils.sign_sha256(pnconf_pam.secret_key, sign_input).rstrip("=")
        })

    def test_audit_channel_group(self):
        self.audit.channel_groups(['gr1', 'gr2'])

        self.assertEqual(self.audit.build_path(), Audit.AUDIT_PATH % pnconf_pam.subscribe_key)

        pam_args = utils.prepare_pam_arguments({
            'timestamp': 123,
            'channel-group': 'gr1,gr2',
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid
        })
        sign_input = HttpMethod.string(self.audit.http_method()).upper() + "\n" + \
            pnconf_pam.publish_key + "\n" + \
            self.audit.build_path() + "\n" + \
            pam_args + "\n"
        self.assertEqual(self.audit.build_params_callback()({}), {
            'pnsdk': sdk_name,
            'uuid': self.pubnub.uuid,
            'timestamp': '123',
            'channel-group': 'gr1,gr2',
            'signature': "v2." + utils.sign_sha256(pnconf_pam.secret_key, sign_input).rstrip("=")
        })
