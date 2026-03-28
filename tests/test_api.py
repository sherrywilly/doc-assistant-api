"""Tests for the FastAPI backend endpoints."""

import io
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "message" in body
    assert "running" in body["message"].lower() or "AI" in body["message"]


# ---------------------------------------------------------------------------
# Upload endpoint
# ---------------------------------------------------------------------------


class TestUploadEndpoint:
    def test_upload_returns_200(self, client, sample_pdf_bytes):
        with patch("app.routes.document.process_document", return_value=MagicMock()):
            response = client.post(
                "/api/v1/upload/my-doc",
                files={
                    "file": ("test.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
                },
            )
        assert response.status_code == 200

    def test_upload_returns_doc_id_in_body(self, client, sample_pdf_bytes):
        with patch("app.routes.document.process_document", return_value=MagicMock()):
            response = client.post(
                "/api/v1/upload/doc-123",
                files={
                    "file": (
                        "report.pdf",
                        io.BytesIO(sample_pdf_bytes),
                        "application/pdf",
                    )
                },
            )
        data = response.json()
        assert data["doc_id"] == "doc-123"

    def test_upload_returns_success_message(self, client, sample_pdf_bytes):
        with patch("app.routes.document.process_document", return_value=MagicMock()):
            response = client.post(
                "/api/v1/upload/msg-doc",
                files={
                    "file": ("f.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
                },
            )
        assert "message" in response.json()

    def test_upload_stores_vectorstore(self, client, sample_pdf_bytes):
        import app.routes.document as doc_module

        mock_vs = MagicMock()
        with patch("app.routes.document.process_document", return_value=mock_vs):
            client.post(
                "/api/v1/upload/stored-doc",
                files={
                    "file": ("f.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
                },
            )
        assert "stored-doc" in doc_module.vectorstores
        assert doc_module.vectorstores["stored-doc"] is mock_vs

    def test_upload_replaces_existing_doc(self, client, sample_pdf_bytes):
        import app.routes.document as doc_module

        vs1, vs2 = MagicMock(), MagicMock()
        with patch("app.routes.document.process_document", return_value=vs1):
            client.post(
                "/api/v1/upload/dup-doc",
                files={
                    "file": ("a.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
                },
            )
        with patch("app.routes.document.process_document", return_value=vs2):
            client.post(
                "/api/v1/upload/dup-doc",
                files={
                    "file": ("b.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
                },
            )
        assert doc_module.vectorstores["dup-doc"] is vs2


# ---------------------------------------------------------------------------
# Ask endpoint
# ---------------------------------------------------------------------------


class TestAskEndpoint:
    def test_ask_unknown_doc_returns_404(self, client):
        response = client.post(
            "/api/v1/ask/unknown-id", params={"question": "Hello?"}
        )
        assert response.status_code == 404

    def test_ask_unknown_doc_has_detail(self, client):
        response = client.post(
            "/api/v1/ask/ghost-doc", params={"question": "Anything?"}
        )
        assert "detail" in response.json()

    def test_ask_success_returns_200(self, client, sample_pdf_bytes):
        mock_vs = MagicMock()
        with patch("app.routes.document.process_document", return_value=mock_vs):
            client.post(
                "/api/v1/upload/qa-doc",
                files={
                    "file": ("f.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
                },
            )
        with patch("app.routes.document.answer_question", return_value="Paris"):
            response = client.post(
                "/api/v1/ask/qa-doc", params={"question": "Capital of France?"}
            )
        assert response.status_code == 200

    def test_ask_returns_correct_answer(self, client, sample_pdf_bytes):
        mock_vs = MagicMock()
        with patch("app.routes.document.process_document", return_value=mock_vs):
            client.post(
                "/api/v1/upload/ans-doc",
                files={
                    "file": ("f.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
                },
            )
        with patch("app.routes.document.answer_question", return_value="42"):
            response = client.post(
                "/api/v1/ask/ans-doc",
                params={"question": "What is the answer?"},
            )
        assert response.json()["answer"] == "42"

    def test_ask_echoes_question_in_response(self, client, sample_pdf_bytes):
        mock_vs = MagicMock()
        with patch("app.routes.document.process_document", return_value=mock_vs):
            client.post(
                "/api/v1/upload/echo-doc",
                files={
                    "file": ("f.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
                },
            )
        question = "What year was this written?"
        with patch("app.routes.document.answer_question", return_value="2024"):
            response = client.post(
                "/api/v1/ask/echo-doc", params={"question": question}
            )
        assert response.json()["question"] == question

    def test_ask_calls_answer_question_with_correct_args(
        self, client, sample_pdf_bytes
    ):
        mock_vs = MagicMock()
        with patch("app.routes.document.process_document", return_value=mock_vs):
            client.post(
                "/api/v1/upload/args-doc",
                files={
                    "file": ("f.pdf", io.BytesIO(sample_pdf_bytes), "application/pdf")
                },
            )
        with patch(
            "app.routes.document.answer_question", return_value="yes"
        ) as mock_answer:
            client.post(
                "/api/v1/ask/args-doc", params={"question": "Is this a test?"}
            )
        mock_answer.assert_called_once_with(mock_vs, "Is this a test?")


# ---------------------------------------------------------------------------
# CORS headers
# ---------------------------------------------------------------------------


def test_cors_header_present_on_get(client):
    """CORS allow-origin header should be present on real GET requests."""
    response = client.get("/", headers={"Origin": "http://localhost:3000"})
    assert response.headers.get("access-control-allow-origin") in (
        "*",
        "http://localhost:3000",
    )


def test_cors_preflight_returns_200(client):
    """CORS preflight OPTIONS request should succeed."""
    response = client.options(
        "/api/v1/ask/any",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
