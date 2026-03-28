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
    """Return a synchronous FastAPI TestClient with auth bypassed."""
    from app.main import app
    from app.core.security import get_current_user

    # Override JWT auth so tests don't need a real token
    app.dependency_overrides[get_current_user] = lambda: "testuser"
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def unauthed_client():
    """Return a TestClient WITHOUT the auth override (for 401 tests)."""
    from app.main import app

    app.dependency_overrides.clear()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


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


# ---------------------------------------------------------------------------
# Auth service fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def test_auth_database_url(tmp_path_factory):
    """Ephemeral SQLite database URL for auth service tests."""
    db_file = tmp_path_factory.mktemp("auth") / "test.db"
    return f"sqlite:///{db_file}"


@pytest.fixture
def auth_client(test_auth_database_url):
    """TestClient for the auth service backed by a temp DB."""
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from auth_service.app.main import app as auth_app
    from auth_service.app.database import Base, get_db

    engine = create_engine(
        test_auth_database_url,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    auth_app.dependency_overrides[get_db] = override_get_db
    with TestClient(auth_app) as c:
        yield c
    auth_app.dependency_overrides.clear()
