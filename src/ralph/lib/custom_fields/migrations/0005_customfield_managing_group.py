# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0006_require_contenttypes_0002'),
        ('custom_fields', '0004_auto_20161214_1126'),
    ]

    operations = [
        migrations.AddField(
            model_name='customfield',
            name='managing_group',
            field=models.ForeignKey(blank=True, null=True, help_text='When set, only members of the specified group will be allowed to set, change or unset values of this custom field for objects.', to='auth.Group', on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
