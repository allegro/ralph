# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ssl_certificates", "0005_auto_20200909_1012"),
    ]

    operations = [
        migrations.AddField(
            model_name="sslcertificate",
            name="certificate_repository",
            field=models.CharField(
                verbose_name="certificate repository",
                max_length=255,
                blank=True,
                help_text="Certificate source repository",
            ),
        ),
    ]
