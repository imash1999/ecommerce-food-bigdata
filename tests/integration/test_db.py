"""
Интеграционные тесты схемы PostgreSQL, созданной scripts/sql/init.sql.

Запуск:
    docker compose up -d postgres
    docker cp scripts/sql/init.sql postgres:/tmp/init.sql
    docker exec postgres psql -U postgres -d postgres -f /tmp/init.sql
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

        expected = {
            "realtime_metrics",
            "realtime_order_metrics",
            "rfm_analysis",
        }
        missing = expected - tables
        assert not missing, f"Missing tables: {missing}"


@pytest.mark.integration
class TestRFMAnalysisTable:
    def test_rfm_analysis_columns(self, db_conn):
        cur = db_conn.cursor()
        cur.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = 'rfm_analysis';
        """)
        columns = {row[0] for row in cur.fetchall()}
        cur.close()

        expected = {
            "user_id",
            "recency",
            "frequency",
            "monetary",
            "rfm_score",
            "updated_at",
        }
        assert expected.issubset(columns)