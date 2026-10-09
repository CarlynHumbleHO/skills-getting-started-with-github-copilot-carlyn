from copy import deepcopy

import pytest


def test_root_redirects_to_index(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_complete_data(client, sample_activities):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == sample_activities


@pytest.mark.parametrize("activity_name", ["Chess Club", "Art Club"])
def test_signup_updates_activity(client, sample_activities, activity_name):
    email = "new+student@example.com"
    expected = deepcopy(sample_activities)
    expected[activity_name]["participants"].append(email)

    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    activities_response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activities_response.status_code == 200
    assert activities_response.json() == expected


def test_duplicate_signup_leaves_activities_unchanged(client, sample_activities):
    email = sample_activities["Chess Club"]["participants"][0]

    response = client.post(
        "/activities/Chess Club/signup", params={"email": email}
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }
    assert client.get("/activities").json() == sample_activities


@pytest.mark.parametrize(
    "method, endpoint", [("POST", "signup"), ("DELETE", "participants")]
)
def test_unknown_activity_leaves_activities_unchanged(
    client, sample_activities, method, endpoint
):
    email = "student@example.com"

    response = client.request(
        method, f"/activities/Unknown Club/{endpoint}", params={"email": email}
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert client.get("/activities").json() == sample_activities


@pytest.mark.parametrize(
    "method, endpoint", [("POST", "signup"), ("DELETE", "participants")]
)
def test_missing_email_leaves_activities_unchanged(
    client, sample_activities, method, endpoint
):
    response = client.request(method, f"/activities/Chess Club/{endpoint}")

    assert response.status_code == 422
    assert any(
        error["loc"] == ["query", "email"]
        for error in response.json()["detail"]
    )
    assert client.get("/activities").json() == sample_activities


@pytest.mark.parametrize("remove_last_participant", [False, True])
def test_remove_participant_updates_activity(
    client, isolated_activities, remove_last_participant
):
    activity_name = "Chess Club"
    email = "existing@example.com"
    if remove_last_participant:
        isolated_activities[activity_name]["participants"] = [email]
    expected = deepcopy(isolated_activities)
    expected[activity_name]["participants"].remove(email)

    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )
    activities_response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert activities_response.status_code == 200
    assert activities_response.json() == expected


@pytest.mark.parametrize("activity_name", ["Chess Club", "Art Club"])
def test_remove_unregistered_participant_leaves_activities_unchanged(
    client, sample_activities, activity_name
):
    email = "unregistered@example.com"

    response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert client.get("/activities").json() == sample_activities


def test_signup_then_removal_restores_activity(client, sample_activities):
    activity_name = "Art Club"
    email = "roundtrip+student@example.com"
    expected_signup = deepcopy(sample_activities)
    expected_signup[activity_name]["participants"].append(email)

    signup_response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )
    after_signup = client.get("/activities")
    removal_response = client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )
    after_removal = client.get("/activities")

    assert signup_response.status_code == 200
    assert after_signup.status_code == 200
    assert after_signup.json() == expected_signup
    assert removal_response.status_code == 200
    assert after_removal.status_code == 200
    assert after_removal.json() == sample_activities