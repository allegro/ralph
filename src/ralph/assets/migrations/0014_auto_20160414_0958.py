# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0013_auto_20160412_1222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ethernet',
            name='label',
            field=ralph.lib.mixins.fields.NullableCharField(max_length=255, blank=True, null=True, verbose_name='name'),
        ),
    ]
