"""i_row_level_security: lock the public schema down to the API's own role

Supabase exposes every table in `public` through PostgREST to the `anon` and
`authenticated` roles. Pozzy never uses that path (Vue only talks to Flask, which
connects as the `postgres` owner role), so those roles get no privileges at all
and row level security is switched on for every table. The owner role bypasses
RLS, so the API is unaffected. Postgres only; tests run on SQLite via create_all.

Every later migration that creates a table must end with
`op.execute("ALTER TABLE <name> ENABLE ROW LEVEL SECURITY")` (CLAUDE.md rule 11).

Revision ID: i1000000rls
Revises: h1000000hours
Create Date: 2026-09-23
"""
from alembic import op

revision = 'i1000000rls'
down_revision = 'h1000000hours'
branch_labels = None
depends_on = None

ROLES = ('anon', 'authenticated')


def _postgres() -> bool:
    return op.get_bind().dialect.name == 'postgresql'


def upgrade():
    if not _postgres():
        return
    op.execute(
        """
        DO $$
        DECLARE r record;
        BEGIN
          FOR r IN SELECT c.relname FROM pg_class c
                   WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r'
          LOOP
            EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', r.relname);
          END LOOP;
        END $$;
        """
    )
    for role in ROLES:
        op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA public FROM {role}")
        op.execute(f"REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM {role}")
        op.execute(f"REVOKE ALL ON ALL FUNCTIONS IN SCHEMA public FROM {role}")
        # Tables created by later migrations get no grants either.
        op.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON TABLES FROM {role}")
        op.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON SEQUENCES FROM {role}")
        op.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public REVOKE ALL ON FUNCTIONS FROM {role}")


def downgrade():
    if not _postgres():
        return
    for role in ROLES:
        op.execute(f"GRANT ALL ON ALL TABLES IN SCHEMA public TO {role}")
        op.execute(f"GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO {role}")
        op.execute(f"GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO {role}")
        op.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO {role}")
        op.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO {role}")
        op.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON FUNCTIONS TO {role}")
    op.execute(
        """
        DO $$
        DECLARE r record;
        BEGIN
          FOR r IN SELECT c.relname FROM pg_class c
                   WHERE c.relnamespace = 'public'::regnamespace AND c.relkind = 'r'
          LOOP
            EXECUTE format('ALTER TABLE public.%I DISABLE ROW LEVEL SECURITY', r.relname);
          END LOOP;
        END $$;
        """
    )
