# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("security", "0002_auto_20160307_1138"),
    ]

    operations = [
        migrations.AlterField(
            model_name="securityscan",
            name="vulnerabilities",
            field=models.ManyToManyField(blank=True, to="security.Vulnerability"),
        ),
    ]
