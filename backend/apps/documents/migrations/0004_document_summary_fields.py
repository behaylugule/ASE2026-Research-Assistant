from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0003_alter_document_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="summary_json",
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="document",
            name="summary_status",
            field=models.CharField(
                choices=[
                    ("none", "None"),
                    ("processing", "Processing"),
                    ("completed", "Completed"),
                    ("failed", "Failed"),
                ],
                default="none",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="document",
            name="summary_updated_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
