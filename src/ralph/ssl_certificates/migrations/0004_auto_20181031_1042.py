# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ssl_certificates", "0003_remove_sslcertificate_service_environment"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sslcertificate",
            name="business_owner",
        ),
        migrations.RemoveField(
            model_name="sslcertificate",
            name="technical_owner",
        ),
    ]
