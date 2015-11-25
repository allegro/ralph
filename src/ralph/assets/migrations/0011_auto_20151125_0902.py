# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0010_service_env_inherits_base_object'),
    ]

    operations = [
        migrations.RenameField(
            model_name='genericcomponent',
            old_name='asset',
            new_name='base_object',
        ),
    ]
