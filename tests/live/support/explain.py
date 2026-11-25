"""pytest plugin: a failed test (or setup or teardown) whose exception is, or wraps through __cause__ or __context__, a
PubNub SDK error gets a "PubNub error" section with category, status code, operation and the service's error data.
Everything goes through redact.scrub, because SDK errors can carry request URLs."""
import pytest
from pubnub.exceptions import PubNubAsyncioException, PubNubException

from . import redact


def _chain(error):
    seen = set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        yield error
        error = error.__cause__ or error.__context__


def describe(error):
    for e in _chain(error):
        if isinstance(e, (PubNubException, PubNubAsyncioException)):
            status = getattr(e, 'status', None)
            parts = [f'type={type(e).__name__}']
            if isinstance(e, PubNubException):
                parts.append(f'status_code={e.get_status_code()}')
                parts.append(f'pn_error={getattr(e, "_pn_error", None)}')
            if status is not None:
                category = getattr(status, 'category', None)
                parts.append(f'category={getattr(category, "name", category)}')
                parts.append(f'operation={getattr(status, "operation", None)}')
                parts.append(f'status_code={getattr(status, "status_code", None)}')
                error_data = getattr(status, 'error_data', None)
                if error_data is not None:
                    parts.append(f'error_data={getattr(error_data, "information", error_data)}')
            return redact.scrub(', '.join(parts))
    return None


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.failed and call.excinfo is not None:
        text = describe(call.excinfo.value)
        if text:
            report.sections.append((f'PubNub error ({report.when})', text))
