from django.db import migrations


CONSTRAINT_NAME = "adolescentes_adolescente_pg_id_fk"
TABLE_NAME = "adolescentes_adolescente"
FK_TABLE_NAME = "adolescentes_pequenogrupo"

# PostgreSQL-safe creation: only add if it doesn't exist
FORWARD_SQL = f"""
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints tc
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = '{TABLE_NAME}'
          AND tc.constraint_name = '{CONSTRAINT_NAME}'
    ) THEN
        ALTER TABLE {TABLE_NAME}
        ADD CONSTRAINT {CONSTRAINT_NAME}
        FOREIGN KEY (pg_id)
        REFERENCES {FK_TABLE_NAME} (id)
        ON DELETE SET NULL
        DEFERRABLE INITIALLY DEFERRED;
    END IF;
END$$;
"""

# Drop if exists (idempotent)
REVERSE_SQL = f"""
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.table_constraints tc
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND tc.table_name = '{TABLE_NAME}'
          AND tc.constraint_name = '{CONSTRAINT_NAME}'
    ) THEN
        ALTER TABLE {TABLE_NAME}
        DROP CONSTRAINT {CONSTRAINT_NAME};
    END IF;
END$$;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("adolescentes", "0014_contagemvisitantes"),
    ]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: (
                schema_editor.execute(FORWARD_SQL)
                if schema_editor.connection.vendor == "postgresql"
                else None
            ),
            reverse_code=lambda apps, schema_editor: (
                schema_editor.execute(REVERSE_SQL)
                if schema_editor.connection.vendor == "postgresql"
                else None
            ),
        ),
    ]
