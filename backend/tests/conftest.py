"""
Test configuration for OVM alert engine smoke tests.

These tests verify alert lifecycle logic using AsyncMock — no real database
required.  They exercise AlertService, AlertRepository interaction, and
deduplication behavior at the service layer.
"""
import uuid
import pytest


@pytest.fixture
def org_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def entity_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()
