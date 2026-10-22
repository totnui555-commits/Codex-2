import pytest
from company_os.settings import Settings, settings
from company_os.temporal_connection import connect_temporal


def test_managed_database_url_preserves_credentials_query_and_installed_driver():
    value = "postgres://service:encoded%40password@db.internal:5432/company?sslmode=require"
    config = Settings(_env_file=None, database_url=value)
    assert config.database_url == value.replace("postgres://", "postgresql+psycopg://", 1)
    assert (
        Settings(_env_file=None, database_url="postgresql://host/db").database_url
        == "postgresql+psycopg://host/db"
    )


async def test_temporal_never_sends_api_key_over_plaintext(monkeypatch):
    monkeypatch.setattr(settings(), "temporal_api_key", "not-a-real-test-key")
    monkeypatch.setattr(settings(), "temporal_tls", False)
    with pytest.raises(ValueError, match="requires TLS"):
        await connect_temporal()
