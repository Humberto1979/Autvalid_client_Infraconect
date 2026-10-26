import os

import psycopg
import pytest

os.environ.setdefault("DB_HOST", os.environ.get("TEST_DB_HOST", "localhost"))
os.environ.setdefault("DB_PORT", os.environ.get("TEST_DB_PORT", "5432"))
os.environ.setdefault("DB_NAME", os.environ.get("TEST_DB_NAME", "infraconect_test"))
os.environ.setdefault("DB_USER", os.environ.get("TEST_DB_USER", "app"))
os.environ.setdefault("DB_PASSWORD", os.environ.get("TEST_DB_PASSWORD", "changeme"))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session")
def db_url(settings) -> str:
    return settings.database_url


@pytest.fixture(scope="session", autouse=True)
def _migrate(db_url):
    # Base limpa + migracoes REAIS do projeto: o proprio `app.migrate` aplica
    # o schema (F12), garantindo paridade entre schema de teste e producao.
    with psycopg.connect(db_url) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS records;")
            cur.execute("DROP TABLE IF EXISTS schema_migrations;")

    from app.migrate import main as run_migrations

    assert run_migrations() == 0
    yield


@pytest.fixture()
def client():
    app = create_app()
    app.testing = True
    with app.test_client() as c:
        yield c