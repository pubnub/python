from pubnub.models.consumer.plugin import Plugin, HookPoint

def spaces_metadata():
    raise ("This will get implemented")

spaces_metadata_plugin = Plugin(
    HookPoint.PubNubCore,
    'spaces_metadata',
    spaces_metadata
)


entity_plugins = [spaces_metadata_plugin]