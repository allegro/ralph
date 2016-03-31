# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('external_services', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='job',
            old_name='params',
            new_name='_dumped_params',
        ),
    ]
