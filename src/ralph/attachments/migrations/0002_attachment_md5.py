# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from ralph.attachments.models import Attachment


def update_md5_checksum(apps, schema_editor):
    for item in Attachment.objects.all():
        item.md5 = item.get_md5_sum()
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachment',
            name='md5',
            field=models.CharField(
                default=None, max_length=32, blank=True, null=True
            ),
            preserve_default=False,
        ),
        migrations.RunPython(update_md5_checksum),
    ]
