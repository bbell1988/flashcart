from httpx import AsyncClient

from tests.conftest import register_and_login


async def test_register_creates_user_and_hashes_password(client: AsyncClient):
    response = await client.post(
        "/register",
        json={"name": "Alice", "email": "alice@example.com", "password": "secret123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert body["role"] == "customer"
    # the response must never echo back the password or its hash
    assert "password" not in body
    assert "password_hash" not in body


async def test_register_duplicate_email_returns_409(client: AsyncClient):
    payload = {"name": "Bob", "email": "bob@example.com", "password": "pw1"}
    first = await client.post("/register", json=payload)
    assert first.status_code == 200

    second = await client.post("/register", json={**payload, "name": "Bob Two"})
    assert second.status_code == 409
    assert second.json()["detail"] == "email already registered"


async def test_login_success_returns_token(client: AsyncClient):
    await client.post(
        "/register", json={"name": "Carol", "email": "carol@example.com", "password": "pw2"}
    )
    response = await client.post(
        "/auth/login", json={"email": "carol@example.com", "password": "pw2"}
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


async def test_login_wrong_password_returns_401(client: AsyncClient):
    await client.post(
        "/register", json={"name": "Dave", "email": "dave@example.com", "password": "correct-pw"}
    )
    response = await client.post(
        "/auth/login", json={"email": "dave@example.com", "password": "wrong-pw"}
    )
    assert response.status_code == 401


async def test_login_nonexistent_email_returns_same_401_message(client: AsyncClient):
    """Prevents user enumeration: wrong password and nonexistent email must be
    indistinguishable from the response alone."""
    await client.post(
        "/register", json={"name": "Erin", "email": "erin@example.com", "password": "pw3"}
    )
    wrong_password = await client.post(
        "/auth/login", json={"email": "erin@example.com", "password": "not-the-password"}
    )
    nonexistent_email = await client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "whatever"}
    )
    assert wrong_password.status_code == nonexistent_email.status_code == 401
    assert wrong_password.json()["detail"] == nonexistent_email.json()["detail"]


async def test_me_requires_authentication(client: AsyncClient):
    response = await client.get("/me")
    assert response.status_code == 401


async def test_me_returns_current_user_with_valid_token(client: AsyncClient):
    token = await register_and_login(client, "frank@example.com", "pw4", name="Frank")
    response = await client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "frank@example.com"
