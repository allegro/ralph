# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assets", "0027_asset_buyout_date"),
        ("ssl_certificates", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="sslcertificate",
            name="domain_ssl",
            field=models.CharField(
                max_length=255,
                verbose_name="domain name",
                blank=True,
                help_text="Full domain name",
            ),
        ),
        migrations.AddField(
            model_name="sslcertificate",
            name="service_environment",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="service_environment",
                to="assets.ServiceEnvironment",
                null=True,
            ),
        ),
    ]
