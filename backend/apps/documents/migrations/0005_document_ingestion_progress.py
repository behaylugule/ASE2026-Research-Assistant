from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0004_document_summary_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="ingestion_progress",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="document",
            name="ingestion_stage",
            field=models.CharField(blank=True, default="", max_length=64),
        ),
    ]
