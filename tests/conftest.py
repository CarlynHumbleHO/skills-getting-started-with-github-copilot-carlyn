from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as backend


@pytest.fixture
def sample_activities():
    return {
        "Chess Club": {
            "description": "Practice chess strategies",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["existing@example.com", "other@example.com"],
        },
        "Art Club": {
            "description": "Explore painting",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": [],
        },
    }


@pytest.fixture(autouse=True)
def isolated_activities(monkeypatch, sample_activities):
    activities = deepcopy(sample_activities)
    monkeypatch.setattr(backend, "activities", activities)
    return activities


@pytest.fixture
def client(isolated_activities):
    with TestClient(backend.app) as test_client:
        yield test_client