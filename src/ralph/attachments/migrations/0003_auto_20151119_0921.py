# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0002_attachment_md5'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='md5',
            field=models.CharField(max_length=32, unique=True),
        ),
    ]
