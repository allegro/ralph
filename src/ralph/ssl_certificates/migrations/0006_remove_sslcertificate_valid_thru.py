# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ssl_certificates', '0005_auto_20180410_1440'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sslcertificate',
            name='valid_thru',
        ),
    ]
