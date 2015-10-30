# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licences', '0003_licence_property_of'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='SoftwareCategory',
            new_name='Software',
        ),
        migrations.RenameField(
            model_name='licence',
            old_name='software_category',
            new_name='software',
        ),
    ]
