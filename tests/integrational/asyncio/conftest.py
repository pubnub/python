import asyncio
import pytest


@pytest.fixture(autouse=True)
def event_loop_for_sync_tests():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        yield
        loop.close()
    else:
        yield
