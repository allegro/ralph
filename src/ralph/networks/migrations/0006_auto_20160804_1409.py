# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.networks.fields


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0005_network_gateway'),
    ]

    operations = [
        migrations.AlterField(
            model_name='network',
            name='address',
            field=ralph.networks.fields.IPNetwork(verbose_name='network address', unique=True, help_text='Presented as string (e.g. 192.168.0.0/24)', max_length=44),
        ),
    ]
