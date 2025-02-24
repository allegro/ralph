# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("networks", "0009_auto_20160823_0921"),
        ("data_center", "0019_dchost"),
    ]

    operations = [
        migrations.AddField(
            model_name="vip",
            name="ip",
            field=models.ForeignKey(
                default=1,
                to="networks.IPAddress",
                on_delete=django.db.models.deletion.CASCADE,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="vip",
            name="name",
            field=models.CharField(default="", max_length=255, verbose_name="name"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="vip",
            name="port",
            field=models.PositiveIntegerField(default=0, verbose_name="port"),
        ),
        migrations.AddField(
            model_name="vip",
            name="protocol",
            field=models.PositiveIntegerField(
                default=1, choices=[(1, "TCP"), (2, "UDP")], verbose_name="protocol"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="vip",
            unique_together=set([("ip", "port", "protocol")]),
        ),
    ]
