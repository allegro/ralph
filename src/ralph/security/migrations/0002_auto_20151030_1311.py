# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('security', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vulnerability',
            name='external_vulnerability_id',
            field=models.IntegerField(help_text='Id of vulnerability from external system', unique=True, blank=True, null=True),
        ),
    ]
