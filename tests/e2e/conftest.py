"""Service-availability guard for e2e tests.

All e2e tests are auto-skipped when the required services are not reachable.
Start them with `make up` before running `make test-e2e` or `make test-e2e-cc`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import requests
import pytest

from helpers import AUTH_SERVER_URL, RESOURCE_SERVER_URL


def _reachable(url: str) -> bool:
    try:
        requests.get(f"{url}/health", timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        return False


@pytest.fixture(scope="session", autouse=True)
def require_services():
    missing = []
    if not _reachable(AUTH_SERVER_URL):
        missing.append(f"auth-server ({AUTH_SERVER_URL})")
    if not _reachable(RESOURCE_SERVER_URL):
        missing.append(f"resource-server ({RESOURCE_SERVER_URL})")
    if missing:
        pytest.skip(f"Services not running: {', '.join(missing)}. Run `make up` first.")
