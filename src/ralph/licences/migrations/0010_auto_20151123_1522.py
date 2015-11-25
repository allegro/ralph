# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime

from ralph.assets.migrations._helpers import InheritFromBaseObject



class Migration(migrations.Migration):

    dependencies = [
        ('licences', '0009_auto_20151120_1817'),
    ]

    operations = [
        migrations.RenameField('Licence', 'remarks', 'remarks2'),
        InheritFromBaseObject('licences', 'Licence', {'remarks': 'remarks2'}),
        migrations.RemoveField(
            model_name='licence',
            name='remarks2',
        ),
        migrations.RemoveField(
            model_name='licence',
            name='created',
        ),
        migrations.RemoveField(
            model_name='licence',
            name='modified',
        ),
        migrations.RemoveField(
            model_name='licence',
            name='tags',
        ),
    ]
