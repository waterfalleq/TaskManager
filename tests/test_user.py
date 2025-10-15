import pytest
from fastapi.testclient import TestClient


# Get current user info
def test_get_current_user(client, test_user):
    response = client.get("/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == test_user.id


# Update email successfully
def test_update_email_success(client):
    new_email = "updated@example.com"
    response = client.patch("/users/email", json={"email": new_email})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == new_email


# Fail to update email to one that already exists
def test_update_email_duplicate(client, db_session):
    from app.models.models import User
    from datetime import datetime, timezone

    existing = User(
        email="taken@example.com",
        hashed_password="fake",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(existing)
    db_session.commit()

    response = client.patch("/users/email", json={"email": "taken@example.com"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


# Update password successfully
def test_update_password_success(client):
    old_password = "Strong1!"
    new_password = "NewStrong1@"

    response = client.patch(
        "/users/password",
        json={"old_password": old_password, "new_password": new_password},
    )
    assert response.status_code == 200
    assert response.json()["detail"] == "Password updated successfully"


# Fail to update password with wrong old password
def test_update_password_wrong_old(client):
    response = client.patch(
        "/users/password",
        json={"old_password": "WrongOld1!", "new_password": "NewStrong1@"},
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect password"


# Fail to update password with weak new password
@pytest.mark.parametrize(
    "new_password", ["short", "nocaps123!", "NOLOWER123!", "NoNumber!", "NoSpecial123"]
)
def test_update_password_invalid_new(client, new_password):
    response = client.patch(
        "/users/password",
        json={"old_password": "Strong1!", "new_password": new_password},
    )
    assert response.status_code == 422
