from django.db import migrations

SQL_ENABLE_EXT = """
CREATE EXTENSION IF NOT EXISTS pg_trgm;
"""

SQL_CREATE_INDEX = """
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_adolescente_fullname_trgm
ON adolescentes_adolescente
USING gin ((nome || ' ' || sobrenome) gin_trgm_ops);
"""

SQL_DROP_INDEX = """
DROP INDEX IF EXISTS idx_adolescente_fullname_trgm;
"""

class Migration(migrations.Migration):
    atomic = False  # necessário para usar CONCURRENTLY

    dependencies = [
        ("adolescentes", "0016_alter_adolescente_options"),
    ]

    operations = [
        migrations.RunSQL(SQL_ENABLE_EXT, reverse_sql=migrations.RunSQL.noop),
        migrations.RunSQL(SQL_CREATE_INDEX, reverse_sql=SQL_DROP_INDEX),
    ]
