"""Tests for the Auth microservice."""

import pytest


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_auth_health(auth_client):
    response = auth_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


class TestRegister:
    def test_register_returns_201(self, auth_client):
        response = auth_client.post(
            "/auth/register",
            json={"username": "alice", "password": "strongpass1"},
        )
        assert response.status_code == 201

    def test_register_returns_username(self, auth_client):
        response = auth_client.post(
            "/auth/register",
            json={"username": "bob", "password": "strongpass2"},
        )
        assert response.json()["username"] == "bob"

    def test_register_does_not_return_password(self, auth_client):
        response = auth_client.post(
            "/auth/register",
            json={"username": "carol", "password": "strongpass3"},
        )
        body = response.json()
        assert "password" not in body
        assert "hashed_password" not in body

    def test_register_duplicate_username_returns_400(self, auth_client):
        payload = {"username": "dup_user", "password": "strongpass4"}
        auth_client.post("/auth/register", json=payload)
        response = auth_client.post("/auth/register", json=payload)
        assert response.status_code == 400

    def test_register_short_password_returns_422(self, auth_client):
        response = auth_client.post(
            "/auth/register",
            json={"username": "shortpass", "password": "abc"},
        )
        assert response.status_code == 422

    def test_register_short_username_returns_422(self, auth_client):
        response = auth_client.post(
            "/auth/register",
            json={"username": "ab", "password": "validpassword"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


class TestLogin:
    def _register(self, auth_client, username: str, password: str):
        auth_client.post(
            "/auth/register", json={"username": username, "password": password}
        )

    def test_login_returns_access_token(self, auth_client):
        self._register(auth_client, "dave", "mypassword1")
        response = auth_client.post(
            "/auth/login",
            data={"username": "dave", "password": "mypassword1"},
        )
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_login_returns_bearer_token_type(self, auth_client):
        self._register(auth_client, "eve", "mypassword2")
        response = auth_client.post(
            "/auth/login",
            data={"username": "eve", "password": "mypassword2"},
        )
        assert response.json()["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, auth_client):
        self._register(auth_client, "frank", "mypassword3")
        response = auth_client.post(
            "/auth/login",
            data={"username": "frank", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    def test_login_unknown_user_returns_401(self, auth_client):
        response = auth_client.post(
            "/auth/login",
            data={"username": "ghost", "password": "anypassword"},
        )
        assert response.status_code == 401

    def test_login_token_is_non_empty_string(self, auth_client):
        self._register(auth_client, "grace", "mypassword4")
        response = auth_client.post(
            "/auth/login",
            data={"username": "grace", "password": "mypassword4"},
        )
        token = response.json()["access_token"]
        assert isinstance(token, str) and len(token) > 20


# ---------------------------------------------------------------------------
# Verify endpoint
# ---------------------------------------------------------------------------


class TestVerify:
    def _get_token(self, auth_client, username: str, password: str) -> str:
        auth_client.post(
            "/auth/register", json={"username": username, "password": password}
        )
        r = auth_client.post(
            "/auth/login", data={"username": username, "password": password}
        )
        return r.json()["access_token"]

    def test_verify_valid_token(self, auth_client):
        token = self._get_token(auth_client, "hank", "mypassword5")
        response = auth_client.post("/auth/verify", params={"token": token})
        assert response.status_code == 200
        assert response.json()["valid"] is True
        assert response.json()["username"] == "hank"

    def test_verify_invalid_token_returns_401(self, auth_client):
        response = auth_client.post(
            "/auth/verify", params={"token": "not.a.valid.token"}
        )
        assert response.status_code == 401
