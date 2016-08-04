# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_fields', '0002_customfield_use_as_configuration_variable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customfieldvalue',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True),
        ),
    ]
