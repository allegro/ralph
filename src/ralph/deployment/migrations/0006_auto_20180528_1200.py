# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('deployment', '0005_auto_20180525_1631'),
    ]

    operations = [
        migrations.AlterField(
            model_name='prebootconfiguration',
            name='configuration',
            field=ralph.lib.mixins.fields.NUMPTextField(blank=True),
        ),
    ]
