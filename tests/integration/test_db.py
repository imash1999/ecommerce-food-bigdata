"""
Интеграционные тесты с реальной PostgreSQL.
Требуют запущенного docker compose.

Запуск:
    docker compose up -d postgres
    pytest tests/integration/ -m integration
"""
import os

import pytest

psycopg2 = pytest.importorskip("psycopg2")


@pytest.fixture(scope="module")
def db_conn():
    """Подключение к тестовой БД."""
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "postgres"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", "root"),
    )
    yield conn
    conn.close()


@pytest.mark.integration
class TestSchema:
    def test_tables_exist(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        tables = {row[0] for row in cur.fetchall()}
        cur.close()

        expected = {"users", "restaurants", "dishes", "orders",
                    "order_items", "realtime_metrics"}
        missing = expected - tables
        assert not missing, f"Missing tables: {missing}"


@pytest.mark.integration
class TestUsersTable:
    def test_users_columns(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users';
        """)
        columns = {row[0] for row in cur.fetchall()}
        cur.close()

        expected = {"id", "username", "email", "password_hash", "name", "created_at"}
        assert expected.issubset(columns)