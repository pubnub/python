"""with_placeholders(client, values): a proxy around a PubNub client whose endpoint builders replace placeholder strings
(for example "my_token" or "file_id") with real values at the call boundary. The sample text keeps its placeholder,
nothing is staged. Applies to positional and keyword arguments of the endpoint method and of every builder setter.

Not used by any test yet (prove it on one sample in the pilot, plan Phase 5).
"""


def _swap(value, values):
    if isinstance(value, str) and value in values:
        return values[value]
    if isinstance(value, list):
        return [_swap(v, values) for v in value]
    return value


class _Builder:
    def __init__(self, target, values):
        self._target = target
        self._values = values

    def __getattr__(self, name):
        attr = getattr(self._target, name)
        if not callable(attr) or name in ('sync', 'future', 'pn_async', 'result'):
            return attr

        def call(*args, **kwargs):
            values = self._values
            out = attr(*[_swap(a, values) for a in args], **{k: _swap(v, values) for k, v in kwargs.items()})
            return _Builder(out, self._values) if out is self._target else out
        return call


class _Client:
    def __init__(self, client, values):
        self._client = client
        self._values = values

    def __getattr__(self, name):
        attr = getattr(self._client, name)
        if not callable(attr):
            return attr

        def endpoint(*args, **kwargs):
            values = self._values
            out = attr(*[_swap(a, values) for a in args], **{k: _swap(v, values) for k, v in kwargs.items()})
            return _Builder(out, self._values) if hasattr(out, 'sync') or hasattr(out, 'future') else out
        return endpoint


def with_placeholders(client, values):
    return _Client(client, dict(values))
