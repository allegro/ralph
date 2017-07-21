# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def rewrite_forward(apps, schema_editor):
    TransitionsHistory = apps.get_model('transitions', 'TransitionsHistory')
    for th in TransitionsHistory.objects.all():
        if th.attachment:
            th.attachments.add(th.attachment)


def rewrite_rewind(apps, schema_editor):
    TransitionsHistory = apps.get_model('transitions', 'TransitionsHistory')
    for th in TransitionsHistory.objects.all():
        for i, attachment in enumerate(th.attachments.all()):
            if i == 0:
                th.attachment = attachment
            else:
                print('Attachment {} for transition history ({}) will be lost.'.format(attachment.file.url, th.transition_name))  # noqa


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0003_auto_20160121_1346'),
        ('transitions', '0005_auto_20160606_1420'),
    ]

    operations = [
        migrations.AddField(
            model_name='transitionshistory',
            name='attachments',
            field=models.ManyToManyField(to='attachments.Attachment'),
        ),
        migrations.RunPython(
            rewrite_forward,
            reverse_code=rewrite_rewind
        ),
        migrations.RemoveField(
            model_name='transitionshistory',
            name='attachment',
        ),
    ]
