import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "email,password",
    [("user1@example.com", "StrongPass1!"), ("user2@example.com", "Another1@Pwd")],
)
def test_register_user_success(client: TestClient, email, password):
    # Successful registration
    response = client.post(
        "/auth/register", json={"email": email, "password": password}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert "id" in data


def test_register_user_duplicate_email(client: TestClient):
    # Create first user
    client.post(
        "/auth/register", json={"email": "dup@example.com", "password": "Strong1!"}
    )
    # Try to register again with same email
    response = client.post(
        "/auth/register", json={"email": "dup@example.com", "password": "Strong1!"}
    )
    assert (
        response.status_code == 400 or response.status_code == 409
    )  # depends on your CRUD


@pytest.mark.parametrize(
    "password",
    [
        "short",  # too short
        "nocaps123!",  # no uppercase
        "NOLOWER123!",  # no lowercase
        "NoNumber!",  # no digit
        "NoSpecial123",  # no special char
    ],
)
def test_register_user_invalid_password(client: TestClient, password):
    response = client.post(
        "/auth/register", json={"email": "testpass@example.com", "password": password}
    )
    assert response.status_code == 422


def test_login_success(client: TestClient):
    email = "loginuser@example.com"
    password = "Strong1!"
    client.post("/auth/register", json={"email": email, "password": password})

    # Login
    response = client.post(
        "/auth/token",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient):
    email = "wrongpass@example.com"
    password = "Strong1!"
    client.post("/auth/register", json={"email": email, "password": password})

    response = client.post(
        "/auth/token",
        data={"username": email, "password": "WrongPass1!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect password"


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/auth/token",
        data={"username": "nouser@example.com", "password": "Whatever1!"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User does not exist"
