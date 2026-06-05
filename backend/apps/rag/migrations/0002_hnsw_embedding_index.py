from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rag", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS rag_documentchunk_embedding_hnsw_idx
            ON rag_documentchunk
            USING hnsw (embedding vector_cosine_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS rag_documentchunk_embedding_hnsw_idx;",
        ),
    ]
