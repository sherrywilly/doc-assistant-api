"""Tests for the Streamlit frontend using AppTest.

These tests exercise the UI logic without requiring a running backend or
real PDF files — all network calls are mocked.
"""

from unittest.mock import patch

import pytest
from streamlit.testing.v1 import AppTest

FRONTEND_PATH = "frontend.py"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _logged_in_app() -> AppTest:
    """Return an AppTest instance with an authenticated session."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    at.session_state.logged_in = True
    at.session_state.access_token = "test-token"
    at.session_state.username = "testuser"
    at.run()
    return at


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------


def test_app_renders_without_exception():
    """The app should start without raising any exceptions."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    assert not at.exception


def test_initial_logged_in_is_false():
    """On first load the user must NOT be authenticated."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    assert at.session_state.logged_in is False


def test_initial_doc_id_is_none():
    """On first load no document should be selected."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    assert at.session_state.doc_id is None


def test_initial_messages_list_is_empty():
    """The messages list must start empty."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    assert isinstance(at.session_state.messages, list)
    assert len(at.session_state.messages) == 0


# ---------------------------------------------------------------------------
# Login page (unauthenticated state)
# ---------------------------------------------------------------------------


def test_login_page_shows_when_not_logged_in():
    """Unauthenticated users should see the login form area."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    assert not at.exception
    # Login/register tabs should be present
    assert len(at.tabs) > 0


def test_login_page_has_username_and_password_inputs():
    """The login form must contain username and password fields."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    assert len(at.text_input) >= 1


def test_chat_input_absent_when_not_logged_in():
    """The chat input must NOT appear for unauthenticated users."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    assert len(at.chat_input) == 0


def test_default_api_url_points_to_localhost():
    """The default API URL should target localhost."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    assert "localhost" in at.session_state.api_base_url


def test_default_auth_url_points_to_localhost():
    """The default Auth URL should also target localhost."""
    at = AppTest.from_file(FRONTEND_PATH)
    at.run()
    assert "localhost" in at.session_state.auth_base_url


# ---------------------------------------------------------------------------
# Authenticated state
# ---------------------------------------------------------------------------


def test_logged_in_renders_main_app():
    """Injecting logged_in=True should render the main app without errors."""
    at = _logged_in_app()
    assert not at.exception


def test_logged_in_shows_welcome_info_without_doc():
    """When logged in but no document loaded, welcome info should appear."""
    at = _logged_in_app()
    assert len(at.info) > 0


def test_logged_in_shows_chat_input_with_doc():
    """When logged in and a doc is active, the chat input should appear."""
    at = _logged_in_app()
    at.session_state.doc_id = "abc123"
    at.session_state.uploaded_file_name = "report.pdf"
    at.run()
    assert len(at.chat_input) > 0


def test_logged_in_doc_id_persists():
    """A doc_id set in session state must not be wiped on re-run."""
    at = _logged_in_app()
    at.session_state.doc_id = "xyz789"
    at.session_state.uploaded_file_name = "manual.pdf"
    at.run()
    assert at.session_state.doc_id == "xyz789"


def test_logged_in_sidebar_has_upload_section():
    """The sidebar should contain the Document Upload heading when logged in."""
    at = _logged_in_app()
    sidebar_markdown = " ".join(m.value for m in at.sidebar.markdown)
    assert "Document Upload" in sidebar_markdown


# ---------------------------------------------------------------------------
# API helper: register_user
# ---------------------------------------------------------------------------


def test_register_user_success():
    """register_user returns (True, '') on 201."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 201
        mock_post.return_value.json.return_value = {"id": 1, "username": "alice"}

        from frontend import register_user

        ok, err = register_user("alice", "password1", "http://localhost:8001/auth")

    assert ok is True
    assert err == ""


def test_register_user_duplicate():
    """register_user returns (False, detail) on 400."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 400
        mock_post.return_value.json.return_value = {
            "detail": "Username already registered."
        }

        from frontend import register_user

        ok, err = register_user("alice", "password1", "http://localhost:8001/auth")

    assert ok is False
    assert "already" in err.lower() or "registered" in err.lower()


# ---------------------------------------------------------------------------
# API helper: login_user
# ---------------------------------------------------------------------------


def test_login_user_success():
    """login_user returns (True, token) on 200."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "access_token": "tok123",
            "token_type": "bearer",
        }

        from frontend import login_user

        ok, token = login_user("alice", "password1", "http://localhost:8001/auth")

    assert ok is True
    assert token == "tok123"


def test_login_user_wrong_credentials():
    """login_user returns (False, detail) on 401."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 401
        mock_post.return_value.json.return_value = {
            "detail": "Incorrect username or password."
        }

        from frontend import login_user

        ok, msg = login_user("alice", "wrong", "http://localhost:8001/auth")

    assert ok is False
    assert "Incorrect" in msg or "password" in msg.lower()


def test_login_user_connection_error():
    """login_user returns a friendly message on ConnectionError."""
    import requests as req

    with patch("requests.post", side_effect=req.ConnectionError):
        from frontend import login_user

        ok, msg = login_user("alice", "password1", "http://localhost:8001/auth")

    assert ok is False
    assert "connect" in msg.lower()


# ---------------------------------------------------------------------------
# API helper: upload_document
# ---------------------------------------------------------------------------


def test_upload_document_success():
    """upload_document should return (True, doc_id) on HTTP 200."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "message": "ok",
            "doc_id": "abc",
        }

        from frontend import upload_document

        # Need a token in session_state for the auth header
        import streamlit as st

        st.session_state.access_token = "test-tok"

        success, result = upload_document(
            b"data", "test.pdf", "http://localhost:8000/api/v1"
        )

    assert success is True


def test_upload_document_failure():
    """upload_document should surface API errors gracefully."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 500
        mock_post.return_value.json.return_value = {"detail": "Server error"}

        from frontend import upload_document

        success, msg = upload_document(
            b"data", "bad.pdf", "http://localhost:8000/api/v1"
        )

    assert success is False
    assert "Upload failed" in msg or "error" in msg.lower()


# ---------------------------------------------------------------------------
# API helper: ask_question
# ---------------------------------------------------------------------------


def test_ask_question_success():
    """ask_question should return (True, answer) on HTTP 200."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "question": "Who wrote this?",
            "answer": "Jane Doe",
        }

        from frontend import ask_question

        success, answer = ask_question(
            "Who wrote this?", "doc-1", "http://localhost:8000/api/v1"
        )

    assert success is True
    assert answer == "Jane Doe"


def test_ask_question_not_found():
    """ask_question should return (False, error) on HTTP 404."""
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 404
        mock_post.return_value.json.return_value = {
            "detail": "Document not found. Please upload the document first."
        }

        from frontend import ask_question

        success, msg = ask_question("test", "missing", "http://localhost:8000/api/v1")

    assert success is False
    assert "Error" in msg or "not found" in msg.lower()


def test_ask_question_connection_error():
    """ask_question should catch connection errors and return a friendly message."""
    import requests as req

    with patch("requests.post", side_effect=req.ConnectionError):
        from frontend import ask_question

        success, msg = ask_question("test", "doc-1", "http://localhost:8000/api/v1")

    assert success is False
    assert "connect" in msg.lower()

