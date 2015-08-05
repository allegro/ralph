# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('licences', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='softwarecategory',
            options={'verbose_name_plural': 'software categories'},
        ),
    ]
