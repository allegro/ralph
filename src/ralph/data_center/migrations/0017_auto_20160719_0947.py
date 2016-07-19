# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0016_diskshare_model_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='datacenterasset',
            name='bios_version',
            field=models.CharField(blank=True, null=True, max_length=16, verbose_name='BIOS version'),
        ),
        migrations.AddField(
            model_name='datacenterasset',
            name='firmware_version',
            field=models.CharField(blank=True, null=True, max_length=16, verbose_name='firmware version'),
        ),
    ]
