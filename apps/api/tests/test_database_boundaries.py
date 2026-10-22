import pytest
from sqlalchemy import text, select
from sqlalchemy.exc import DBAPIError
from company_os.db import Session, engine
from company_os.models import Organization, Project


def test_postgres_rls_filters_even_without_application_where_clause(owner_client, project):
    with Session.begin() as db:
        other = Organization(name="Private tenant")
        db.add(other)
        db.flush()
        db.add(Project(organization_id=other.id, name="Invisible project"))
    with engine.begin() as connection:
        connection.execute(text("SET LOCAL ROLE company_api"))
        connection.execute(
            text("SELECT set_config('app.organization_id',:id,true)"), {"id": project["organization_id"]}
        )
        names = connection.execute(text("SELECT name FROM projects")).scalars().all()
        assert names == ["Real test project"]


def test_worker_and_watchtower_cannot_self_authorize_spend(owner_client, project):
    for role in ["company_worker", "company_watchtower"]:
        with pytest.raises(DBAPIError, match="permission denied"):
            with engine.begin() as connection:
                connection.execute(text("SET LOCAL ROLE " + role))
                connection.execute(text("UPDATE organizations SET paid_execution_authorized=true"))
    with pytest.raises(DBAPIError, match="permission denied"):
        with engine.begin() as connection:
            connection.execute(text("SET LOCAL ROLE company_watchtower"))
            connection.execute(text("UPDATE approvals SET state='approved'"))


def test_history_append_only(owner_client, project):
    with pytest.raises(DBAPIError, match="append-only"):
        with engine.begin() as connection:
            connection.execute(text("UPDATE audit_records SET action='forged'"))
