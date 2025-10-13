import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(async_client: AsyncClient):
    """
    Register a new user with a valid password.
    Expect 201 Created and a response containing email and id.
    """
    response = await async_client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "StrongPass1!"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_weak_password(async_client: AsyncClient):
    """
    Try to register with a weak password.
    Expect validation error (422 from Pydantic or 400 from custom validation).
    """
    response = await async_client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "123"}
    )
    assert response.status_code in (400, 422)


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    """
    Register a user and then log in with correct credentials.
    Expect 200 OK and a valid JWT token in the response.
    """
    await async_client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "StrongPass1!"}
    )
    response = await async_client.post(
        "/auth/token",
        data={"username": "login@example.com", "password": "StrongPass1!"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    """
    Register a user and try to log in with an incorrect password.
    Expect 401 Unauthorized with 'Incorrect password' detail.
    """
    await async_client.post(
        "/auth/register",
        json={"email": "wrongpass@example.com", "password": "StrongPass1!"}
    )
    response = await async_client.post(
        "/auth/token",
        data={"username": "wrongpass@example.com", "password": "Wrong123!"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect password"


@pytest.mark.asyncio
async def test_login_user_not_found(async_client: AsyncClient):
    """
    Try to log in with a non-existing user.
    Expect 404 Not Found with 'User does not exist' detail.
    """
    response = await async_client.post(
        "/auth/token",
        data={"username": "nouser@example.com", "password": "StrongPass1!"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "User does not exist"
