# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='backofficeasset',
            name='imei',
            field=ralph.lib.mixins.fields.NullableCharField(null=True, blank=True, unique=True, max_length=18),
        ),
    ]
