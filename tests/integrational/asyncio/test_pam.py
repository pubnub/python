import pytest

from pubnub.models.consumer.access_manager import PNAccessManagerGrantResult, PNAccessManagerAuditResult
from pubnub.pubnub_asyncio import PubNubAsyncio
from tests import helper
from tests.helper import pnconf_pam_copy


@pytest.mark.asyncio
async def test_global_level(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"

    env = (await pubnub.grant()
           .write(True)
           .read(True)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert len(env.result.channels) == 0
    assert len(env.result.groups) == 0
    assert env.result.read_enabled is True
    assert env.result.write_enabled is True
    assert env.result.manage_enabled is False

    env = (await pubnub.audit()
           .future())

    assert isinstance(env.result, PNAccessManagerAuditResult)
    assert len(env.result.channels) >= 0
    assert len(env.result.groups) >= 0
    assert env.result.read_enabled is True
    assert env.result.write_enabled is True
    assert env.result.manage_enabled is False

    pubnub.stop()


@pytest.mark.asyncio
async def test_single_channel(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    ch = helper.gen_channel("pam-channel")

    env = (await pubnub.grant()
           .channels(ch)
           .write(True)
           .read(True)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.channels[ch].read_enabled == 1
    assert env.result.channels[ch].write_enabled == 1
    assert env.result.channels[ch].manage_enabled == 0

    env = (await pubnub.audit()
           .channels(ch)
           .future())

    assert isinstance(env.result, PNAccessManagerAuditResult)
    assert env.result.channels[ch].read_enabled == 1
    assert env.result.channels[ch].write_enabled == 1
    assert env.result.channels[ch].manage_enabled == 0

    pubnub.stop()


@pytest.mark.asyncio
async def test_single_channel_with_auth(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    ch = helper.gen_channel("pam-channel")
    auth = helper.gen_channel("pam-auth-key")

    env = (await pubnub.grant()
           .channels(ch)
           .write(True)
           .read(True)
           .auth_keys(auth)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.channels[ch].auth_keys[auth].read_enabled == 1
    assert env.result.channels[ch].auth_keys[auth].write_enabled == 1
    assert env.result.channels[ch].auth_keys[auth].manage_enabled == 0

    env = (await pubnub.audit()
           .channels(ch)
           .auth_keys(auth)
           .future())

    assert isinstance(env.result, PNAccessManagerAuditResult)
    assert env.result.channels[ch].auth_keys[auth].read_enabled == 1
    assert env.result.channels[ch].auth_keys[auth].write_enabled == 1
    assert env.result.channels[ch].auth_keys[auth].manage_enabled == 0

    pubnub.stop()


@pytest.mark.asyncio
async def test_multiple_channels(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    ch1 = helper.gen_channel("pam-channel")
    ch2 = helper.gen_channel("pam-channel")

    env = (await pubnub.grant()
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

    env = (await pubnub.audit()
           .channels([ch1, ch2])
           .future())

    assert isinstance(env.result, PNAccessManagerAuditResult)
    assert env.result.channels[ch1].read_enabled is True
    assert env.result.channels[ch2].read_enabled is True
    assert env.result.channels[ch1].write_enabled is True
    assert env.result.channels[ch2].write_enabled is True
    assert env.result.channels[ch1].manage_enabled is False
    assert env.result.channels[ch2].manage_enabled is False

    pubnub.stop()


@pytest.mark.asyncio
async def test_multiple_channels_with_auth(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    ch1 = helper.gen_channel("pam-channel")
    ch2 = helper.gen_channel("pam-channel")
    auth = helper.gen_channel("pam-auth-key")

    env = (await pubnub.grant()
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

    env = (await pubnub.audit()
           .channels([ch1, ch2])
           .future())

    assert isinstance(env.result, PNAccessManagerAuditResult)
    assert env.result.channels[ch1].auth_keys[auth].read_enabled is True
    assert env.result.channels[ch2].auth_keys[auth].read_enabled is True
    assert env.result.channels[ch1].auth_keys[auth].write_enabled is True
    assert env.result.channels[ch2].auth_keys[auth].write_enabled is True
    assert env.result.channels[ch1].auth_keys[auth].manage_enabled is False
    assert env.result.channels[ch2].auth_keys[auth].manage_enabled is False

    pubnub.stop()


@pytest.mark.asyncio
async def test_single_channel_group(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    cg = helper.gen_channel("pam-cg")

    env = (await pubnub.grant()
           .channel_groups(cg)
           .write(True)
           .read(True)
           .future())

    assert isinstance(env.result, PNAccessManagerGrantResult)
    assert env.result.level == 'channel-group'
    assert env.result.groups[cg].read_enabled == 1
    assert env.result.groups[cg].write_enabled == 1
    assert env.result.groups[cg].manage_enabled == 0

    env = (await pubnub.audit()
           .channel_groups(cg)
           .future())

    assert isinstance(env.result, PNAccessManagerAuditResult)
    assert env.result.level == 'channel-group'
    assert env.result.groups[cg].read_enabled == 1
    assert env.result.groups[cg].write_enabled == 1
    assert env.result.groups[cg].manage_enabled == 0

    pubnub.stop()


@pytest.mark.asyncio
async def test_single_channel_group_with_auth(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    gr = helper.gen_channel("pam-cg")
    auth = helper.gen_channel("pam-auth-key")

    env = (await pubnub.grant()
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

    env = (await pubnub.audit()
           .channel_groups(gr)
           .auth_keys(auth)
           .future())

    assert isinstance(env.result, PNAccessManagerAuditResult)
    assert env.result.groups[gr].auth_keys[auth].read_enabled == 1
    assert env.result.groups[gr].auth_keys[auth].write_enabled == 1
    assert env.result.groups[gr].auth_keys[auth].manage_enabled == 0

    pubnub.stop()


@pytest.mark.asyncio
async def test_multiple_channel_groups(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    gr1 = helper.gen_channel("pam-group1")
    gr2 = helper.gen_channel("pam-group2")

    env = (await pubnub.grant()
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

    env = (await pubnub.audit()
           .channel_groups([gr1, gr2])
           .future())

    assert isinstance(env.result, PNAccessManagerAuditResult)
    assert env.result.groups[gr1].read_enabled is True
    assert env.result.groups[gr2].read_enabled is True
    assert env.result.groups[gr1].write_enabled is True
    assert env.result.groups[gr2].write_enabled is True
    assert env.result.groups[gr1].manage_enabled is False
    assert env.result.groups[gr2].manage_enabled is False

    pubnub.stop()


@pytest.mark.asyncio
async def test_multiple_channel_groups_with_auth(event_loop):
    pubnub = PubNubAsyncio(pnconf_pam_copy(), custom_event_loop=event_loop)
    pubnub.config.uuid = "my_uuid"
    gr1 = helper.gen_channel("pam-group1")
    gr2 = helper.gen_channel("pam-group2")
    auth = helper.gen_channel("pam-auth-key")

    env = (await pubnub.grant()
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

    env = (await pubnub.audit()
           .channel_groups([gr1, gr2])
           .future())

    assert isinstance(env.result, PNAccessManagerAuditResult)
    assert env.result.groups[gr1].auth_keys[auth].read_enabled is True
    assert env.result.groups[gr2].auth_keys[auth].read_enabled is True
    assert env.result.groups[gr1].auth_keys[auth].write_enabled is True
    assert env.result.groups[gr2].auth_keys[auth].write_enabled is True
    assert env.result.groups[gr1].auth_keys[auth].manage_enabled is False
    assert env.result.groups[gr2].auth_keys[auth].manage_enabled is False

    pubnub.stop()
