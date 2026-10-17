import os
import sys
from unittest.mock import MagicMock, patch

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DAGS = os.path.join(ROOT, "dags")
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, ROOT)
sys.path.insert(0, DAGS)
sys.path.insert(0, BACKEND)


@pytest.fixture(autouse=True)
def test_session_secret(monkeypatch):
    monkeypatch.setenv(
        "ADMIN_SESSION_SECRET",
        "test-only-secret-for-admin-session-tests-0123456789",
    )


@pytest.fixture
def mock_cursor():
    cursor = MagicMock()
    cursor.fetchone.return_value = None
    cursor.fetchall.return_value = []
    return cursor


@pytest.fixture
def mock_conn(mock_cursor):
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    conn.autocommit = True
    return conn


@pytest.fixture
def mock_get_db(mock_conn, mock_cursor):
    with patch("backend.main.get_db_connection", return_value=mock_conn):
        yield mock_conn, mock_cursor


@pytest.fixture
def api_client():
    from fastapi.testclient import TestClient
    from backend.main import app
    return TestClient(app)