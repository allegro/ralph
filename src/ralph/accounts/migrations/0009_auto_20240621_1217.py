# Generated by Django 2.0.13 on 2024-06-21 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_auto_20240507_1422"),
    ]

    operations = [
        migrations.AlterField(
            model_name="ralphuser",
            name="last_name",
            field=models.CharField(
                blank=True, max_length=150, verbose_name="last name"
            ),
        ),
    ]
