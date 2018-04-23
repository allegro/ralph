# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ssl_certificates', '0004_auto_20180409_1552'),
    ]

    operations = [
        migrations.AddField(
            model_name='sslcertificate',
            name='date_from',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='sslcertificate',
            name='date_to',
            field=models.DateField(default=None),
            preserve_default=False,
        ),
    ]
