# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cross_validator', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='crossvalidationresult',
            name='object_pk',
            field=models.IntegerField(db_index=True, null=True),
        ),
    ]
