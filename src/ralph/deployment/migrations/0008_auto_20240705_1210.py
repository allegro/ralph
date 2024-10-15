# Generated by Django 2.0.13 on 2024-07-05 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("deployment", "0007_auto_20240506_1633"),
    ]

    operations = [
        migrations.AddField(
            model_name="preboot",
            name="critical_after",
            field=models.DateField(blank=False, null=True),
        ),
        migrations.AddField(
            model_name="preboot",
            name="disappears_after",
            field=models.DateField(blank=False, null=True),
        ),
        migrations.AddField(
            model_name="preboot",
            name="warning_after",
            field=models.DateField(blank=False, null=True),
        ),
    ]
