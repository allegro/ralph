# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
        ('transitions', '0008_auto_20171211_1300'),
    ]

    operations = [
        migrations.AddField(
            model_name='transition',
            name='success_url',
            field=ralph.lib.mixins.fields.NullableCharField(null=True, max_length=255, default=None, blank=True),
        ),
    ]
