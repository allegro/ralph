# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ssl_certificates', '0002_auto_20180409_1440'),
    ]

    operations = [
        migrations.AddField(
            model_name='sslcertificate',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, default=0, max_digits=10, null=True),
        ),
    ]
