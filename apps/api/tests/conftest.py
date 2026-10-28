"""Pytest fixtures. Integration tests requiring Postgres will be added when Docker is available."""

import pytest


@pytest.fixture
def anyio_backend():
    return "asyncio"
