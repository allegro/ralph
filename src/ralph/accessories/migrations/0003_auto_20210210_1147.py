# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('accessories', '0002_auto_20210210_1111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accessoriesuser',
            name='user',
            field=models.ForeignKey(related_name='user', to=settings.AUTH_USER_MODEL),
        ),
    ]
