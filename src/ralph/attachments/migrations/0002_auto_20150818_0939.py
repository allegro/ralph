# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachmentitem',
            name='attachment',
            field=models.ForeignKey(related_name='items', to='attachments.Attachment'),
        ),
    ]
