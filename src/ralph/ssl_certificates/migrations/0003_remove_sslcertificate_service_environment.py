# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ssl_certificates", "0002_auto_20180522_1244"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="sslcertificate",
            name="service_environment",
        ),
    ]
