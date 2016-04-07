# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('external_services', '0002_auto_20160325_0837'),
    ]

    operations = [
        migrations.RenameField(
            model_name='job',
            old_name='user',
            new_name='username',
        ),
    ]
