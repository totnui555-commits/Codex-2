"""Tenant row policies; provision runtime roles with scripts/database_roles.sql."""

from alembic import op
import sqlalchemy as sa

revision = "76e80001"
down_revision = "7e0439ff7b69"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    tables = connection.execute(
        sa.text(
            "SELECT table_name FROM information_schema.columns WHERE table_schema='public' AND column_name='organization_id'"
        )
    )
    for (table,) in list(tables):
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        expression = "organization_id = current_setting('app.organization_id', true)"
        if table == "memberships":
            expression += " OR user_id = current_setting('app.user_id', true)"
        op.execute(f'CREATE POLICY tenant_scope ON "{table}" USING ({expression}) WITH CHECK ({expression})')
    # Audit and events are append-only to runtime roles (owner migration role is separate).
    op.execute(
        """CREATE FUNCTION prevent_history_mutation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'Operational history is append-only'; END $$"""
    )
    for table in ["audit_records", "events"]:
        op.execute(
            f"CREATE TRIGGER immutable_history BEFORE UPDATE OR DELETE ON {table} FOR EACH ROW EXECUTE FUNCTION prevent_history_mutation()"
        )


def downgrade():
    for table in ["audit_records", "events"]:
        op.execute(f"DROP TRIGGER immutable_history ON {table}")
    op.execute("DROP FUNCTION prevent_history_mutation()")
    connection = op.get_bind()
    tables = connection.execute(
        sa.text(
            "SELECT table_name FROM information_schema.columns WHERE table_schema='public' AND column_name='organization_id'"
        )
    )
    for (table,) in list(tables):
        op.execute(f'DROP POLICY tenant_scope ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
