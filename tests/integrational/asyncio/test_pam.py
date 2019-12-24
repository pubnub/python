import pytest

from pubnub.models.consumer.access_manager import PNAccessManagerGrantResult
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests.helper import pnconf_pam_copy
from tests.integrational.vcr_helper import pn_vcr


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/pam/global_level.yaml',
                     filter_query_parameters=['signature', 'timestamp', 'pnsdk', 'l_pam'])
@pytest.mark.asyncio
def test_global_level(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"

    env = (yield from pubnub.grant()
           .write(True)
           .read(True)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert len(env.result.channels) == 0
    assert len(env.result.groups) == 0
    assert env.result.read_enabled is True
    assert env.result.write_enabled is True
    assert env.result.manage_enabled is False
    assert env.result.delete_enabled is False

    env = yield from pubnub.revoke().future()

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert len(env.result.channels) == 0
    assert len(env.result.groups) == 0
    assert env.result.read_enabled is False
    assert env.result.write_enabled is False
    assert env.result.manage_enabled is False
    assert env.result.delete_enabled is False

    pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/pam/single_channel.yaml',
                     filter_query_parameters=['signature', 'timestamp', 'pnsdk', 'l_pam'])
@pytest.mark.asyncio
def test_single_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    ch = "test-pam-asyncio-ch"

    env = (yield from pubnub.grant()
           .channels(ch)
           .write(True)
           .read(True)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.channels[ch].read_enabled == 1
    assert env.result.channels[ch].write_enabled == 1
    assert env.result.channels[ch].manage_enabled == 0
    assert env.result.channels[ch].delete_enabled == 0

    pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/pam/single_channel_with_auth.yaml',
                     filter_query_parameters=['signature', 'timestamp', 'pnsdk', 'l_pam'])
@pytest.mark.asyncio
def test_single_channel_with_auth(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "test-pam-asyncio-uuid"
    ch = "test-pam-asyncio-ch"
    auth = "test-pam-asyncio-auth"

    env = (yield from pubnub.grant()
           .channels(ch)
           .write(True)
           .read(True)
           .auth_keys(auth)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.channels[ch].auth_keys[auth].read_enabled == 1
    assert env.result.channels[ch].auth_keys[auth].write_enabled == 1
    assert env.result.channels[ch].auth_keys[auth].manage_enabled == 0
    assert env.result.channels[ch].auth_keys[auth].delete_enabled == 0

    pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/pam/multiple_channels.yaml',
                     filter_query_parameters=['signature', 'timestamp', 'pnsdk', 'l_pam'],
                     match_on=['method', 'scheme', 'host', 'port', 'path', 'string_list_in_query'],
                     match_on_kwargs={
                         'list_keys': ['channel'],
                         'filter_keys': ['signature', 'timestamp']
                     })
@pytest.mark.asyncio
def test_multiple_channels(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "test-pam-asyncio-uuid"
    ch1 = "test-pam-asyncio-ch1"
    ch2 = "test-pam-asyncio-ch2"

    env = (yield from pubnub.grant()
           .channels([ch1, ch2])
           .write(True)
           .read(True)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.channels[ch1].read_enabled is True
    assert env.result.channels[ch2].read_enabled is True
    assert env.result.channels[ch1].write_enabled is True
    assert env.result.channels[ch2].write_enabled is True
    assert env.result.channels[ch1].manage_enabled is False
    assert env.result.channels[ch2].manage_enabled is False
    assert env.result.channels[ch1].delete_enabled is False
    assert env.result.channels[ch2].delete_enabled is False

    pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/pam/multiple_channels_with_auth.yaml',
                     filter_query_parameters=['signature', 'timestamp', 'pnsdk', 'l_pam'],
                     match_on=['method', 'scheme', 'host', 'port', 'path', 'string_list_in_query'],
                     match_on_kwargs={
                         'list_keys': ['channel'],
                         'filter_keys': ['signature', 'timestamp']
                     })
@pytest.mark.asyncio
def test_multiple_channels_with_auth(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    ch1 = "test-pam-asyncio-ch1"
    ch2 = "test-pam-asyncio-ch2"
    auth = "test-pam-asyncio-auth"

    env = (yield from pubnub.grant()
           .channels([ch1, ch2])
           .write(True)
           .read(True)
           .auth_keys(auth)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.channels[ch1].auth_keys[auth].read_enabled is True
    assert env.result.channels[ch2].auth_keys[auth].read_enabled is True
    assert env.result.channels[ch1].auth_keys[auth].write_enabled is True
    assert env.result.channels[ch2].auth_keys[auth].write_enabled is True
    assert env.result.channels[ch1].auth_keys[auth].manage_enabled is False
    assert env.result.channels[ch2].auth_keys[auth].manage_enabled is False
    assert env.result.channels[ch1].auth_keys[auth].delete_enabled is False
    assert env.result.channels[ch2].auth_keys[auth].delete_enabled is False

    pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/pam/single_channel_group.yaml',
                     filter_query_parameters=['signature', 'timestamp', 'pnsdk', 'l_pam'])
@pytest.mark.asyncio
def test_single_channel_group(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "test-pam-asyncio-uuid"
    cg = "test-pam-asyncio-cg"

    env = (yield from pubnub.grant()
           .channel_groups(cg)
           .write(True)
           .read(True)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.level == 'channel-group'
    assert env.result.groups[cg].read_enabled == 1
    assert env.result.groups[cg].write_enabled == 1
    assert env.result.groups[cg].manage_enabled == 0
    assert env.result.groups[cg].delete_enabled == 0

    pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/pam/single_channel_group_with_auth.yaml',
                     filter_query_parameters=['signature', 'timestamp', 'pnsdk', 'l_pam'])
@pytest.mark.asyncio
def test_single_channel_group_with_auth(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "test-pam-asyncio-uuid"
    gr = "test-pam-asyncio-cg"
    auth = "test-pam-asyncio-auth"

    env = (yield from pubnub.grant()
           .channel_groups(gr)
           .write(True)
           .read(True)
           .auth_keys(auth)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.level == 'channel-group+auth'
    assert env.result.groups[gr].auth_keys[auth].read_enabled == 1
    assert env.result.groups[gr].auth_keys[auth].write_enabled == 1
    assert env.result.groups[gr].auth_keys[auth].manage_enabled == 0
    assert env.result.groups[gr].auth_keys[auth].delete_enabled == 0

    pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/pam/multiple_channel_groups.yaml',
                     filter_query_parameters=['signature', 'timestamp', 'pnsdk', 'l_pam'],
                     match_on=['method', 'scheme', 'host', 'port', 'path', 'string_list_in_query'],
                     match_on_kwargs={
                         'list_keys': ['channel-group'],
                         'filter_keys': ['signature', 'timestamp']
                     })
@pytest.mark.asyncio
def test_multiple_channel_groups(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    gr1 = "test-pam-asyncio-cg1"
    gr2 = "test-pam-asyncio-cg2"

    env = (yield from pubnub.grant()
           .channel_groups([gr1, gr2])
           .write(True)
           .read(True)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.groups[gr1].read_enabled is True
    assert env.result.groups[gr2].read_enabled is True
    assert env.result.groups[gr1].write_enabled is True
    assert env.result.groups[gr2].write_enabled is True
    assert env.result.groups[gr1].manage_enabled is False
    assert env.result.groups[gr2].manage_enabled is False
    assert env.result.groups[gr1].delete_enabled is False
    assert env.result.groups[gr2].delete_enabled is False

    pubnub.stop()


@pn_vcr.use_cassette('tests/integrational/fixtures/asyncio/pam/multiple_channel_groups_with_auth.yaml',
                     filter_query_parameters=['signature', 'timestamp', 'pnsdk', 'l_pam'],
                     match_on=['method', 'scheme', 'host', 'port', 'path', 'string_list_in_query'],
                     match_on_kwargs={
                         'list_keys': ['channel-group'],
                         'filter_keys': ['signature', 'timestamp']
                     })
@pytest.mark.asyncio
def test_multiple_channel_groups_with_auth(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    gr1 = "test-pam-asyncio-cg1"
    gr2 = "test-pam-asyncio-cg2"
    auth = "test-pam-asyncio-auth"

    env = (yield from pubnub.grant()
           .channel_groups([gr1, gr2])
           .write(True)
           .read(True)
           .auth_keys(auth)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.groups[gr1].auth_keys[auth].read_enabled is True
    assert env.result.groups[gr2].auth_keys[auth].read_enabled is True
    assert env.result.groups[gr1].auth_keys[auth].write_enabled is True
    assert env.result.groups[gr2].auth_keys[auth].write_enabled is True
    assert env.result.groups[gr1].auth_keys[auth].manage_enabled is False
    assert env.result.groups[gr2].auth_keys[auth].manage_enabled is False
    assert env.result.groups[gr1].auth_keys[auth].delete_enabled is False
    assert env.result.groups[gr2].auth_keys[auth].delete_enabled is False

    pubnub.stop()
