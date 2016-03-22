# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0002_auto_20160310_1425'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ipaddress',
            name='base_object',
            field=ralph.lib.mixins.fields.BaseObjectForeignKey(to='assets.BaseObject', on_delete=django.db.models.deletion.SET_NULL, blank=True, null=True, default=None, verbose_name='Base object'),
        ),
    ]
