# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from ralph.assets.migrations._helpers import InheritFromBaseObject


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0009_asset_property_of_rename'),
    ]

    operations = [
        InheritFromBaseObject('assets', 'ServiceEnvironment'),
        migrations.AlterField(
            model_name='baseobject',
            name='parent',
            field=models.ForeignKey(to='assets.BaseObject', null=True, blank=True, related_name='children'),
        ),
    ]
