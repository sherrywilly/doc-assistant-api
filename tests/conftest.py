"""Shared pytest fixtures for the AI Document Assistant test suite."""

import io

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


@pytest.fixture(autouse=True)
def clear_vectorstores():
    """Reset the in-memory vectorstore dict between every test."""
    import app.routes.document as doc_module

    doc_module.vectorstores.clear()
    yield
    doc_module.vectorstores.clear()


@pytest.fixture
def client():
    """Return a synchronous FastAPI TestClient."""
    from app.main import app

    return TestClient(app)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Minimal valid-looking PDF bytes for upload tests."""
    return (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type /Catalog /Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type /Pages /Kids [] /Count 0>>endobj\n"
        b"xref\n0 3\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000058 00000 n\n"
        b"trailer<</Size 3 /Root 1 0 R>>\n"
        b"startxref\n109\n%%EOF"
    )


@pytest.fixture
def mock_vectorstore():
    """A generic mock vectorstore."""
    return MagicMock()
