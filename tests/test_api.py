import copy
import urllib.parse

from fastapi.testclient import TestClient
import pytest

from src.app import app, activities


@pytest.fixture
def client():
    # Arrange: create TestClient for the FastAPI app
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def restore_activities():
    # Arrange: deep-copy activities state before test
    original = copy.deepcopy(activities)
    try:
        yield
    finally:
        # Cleanup: restore original activities after test
        activities.clear()
        activities.update(copy.deepcopy(original))


def test_root_redirect(client):
    # Arrange
    # Act
    resp = client.get("/", allow_redirects=False)
    # Assert
    assert resp.status_code == 307
    assert resp.headers["location"] == "/static/index.html"


def test_get_activities(client):
    # Arrange
    # Act
    resp = client.get("/activities")
    # Assert
    assert resp.status_code == 200
    assert isinstance(resp.json(), dict)
    assert "Chess Club" in resp.json()


def test_signup_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    encoded = urllib.parse.quote(activity_name, safe="")
    url = f"/activities/{encoded}/signup"

    # Ensure clean state
    if email in activities[activity_name]["participants"]:
        activities[activity_name]["participants"].remove(email)

    # Act
    resp = client.post(url, params={"email": email})

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")
    assert email in activities[activity_name]["participants"]


def test_signup_existing(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"
    encoded = urllib.parse.quote(activity_name, safe="")
    url = f"/activities/{encoded}/signup"

    # Act
    resp = client.post(url, params={"email": existing_email})

    # Assert
    assert resp.status_code == 400
    assert resp.json().get("detail") == "Student already signed up for this activity"


def test_signup_nonexistent_activity(client):
    # Arrange
    activity_name = "Nonexistent Club"
    email = "someone@mergington.edu"
    encoded = urllib.parse.quote(activity_name, safe="")
    url = f"/activities/{encoded}/signup"

    # Act
    resp = client.post(url, params={"email": email})

    # Assert
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Activity not found"


def test_remove_participant_success(client):
    # Arrange
    activity_name = "Chess Club"
    participant = "michael@mergington.edu"
    assert participant in activities[activity_name]["participants"]
    encoded = urllib.parse.quote(activity_name, safe="")
    url = f"/activities/{encoded}/participants"

    # Act
    resp = client.delete(url, params={"email": participant})

    # Assert
    assert resp.status_code == 200
    body = resp.json()
    assert "Removed" in body.get("message", "")
    assert participant not in activities[activity_name]["participants"]


def test_remove_participant_not_found(client):
    # Arrange
    activity_name = "Chess Club"
    missing_email = "notfound@mergington.edu"
    assert missing_email not in activities[activity_name]["participants"]
    encoded = urllib.parse.quote(activity_name, safe="")
    url = f"/activities/{encoded}/participants"

    # Act
    resp = client.delete(url, params={"email": missing_email})

    # Assert
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Participant not found for this activity"


def test_data_model_consistency(client):
    # Arrange
    # Act
    resp = client.get("/activities")
    data = resp.json()

    # Assert
    assert isinstance(data, dict)
    for name, item in data.items():
        assert isinstance(name, str)
        assert isinstance(item, dict)
        assert "description" in item
        assert "schedule" in item
        assert "max_participants" in item
        assert "participants" in item
        assert isinstance(item["description"], str)
        assert isinstance(item["schedule"], str)
        assert isinstance(item["max_participants"], int)
        assert isinstance(item["participants"], list)
