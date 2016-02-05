# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('transitions', '0003_auto_20151202_1216'),
    ]

    operations = [
        migrations.AddField(
            model_name='transitionshistory',
            name='diff',
            field=django_extensions.db.fields.json.JSONField(null=True, blank=True),
        ),
    ]
