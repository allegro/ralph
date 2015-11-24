# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from ralph.assets.migrations._helpers import InheritFromBaseObject


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0010_service_env_inherits_base_object'),
        ('supports', '0004_auto_20151119_2158'),
    ]

    operations = [
        migrations.RenameField('Support', 'remarks', 'remarks2'),
        InheritFromBaseObject('supports', 'Support', {'remarks': 'remarks2'}),
        migrations.RemoveField(
            model_name='Support',
            name='remarks2',
        ),
        migrations.RemoveField(
            model_name='Support',
            name='created',
        ),
        migrations.RemoveField(
            model_name='Support',
            name='modified',
        ),
        migrations.RemoveField(
            model_name='Support',
            name='tags',
        ),
    ]
