# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0008_datacenter_show_on_dashboard'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='diskshare',
            name='base_object',
        ),
        migrations.RemoveField(
            model_name='diskshare',
            name='model',
        ),
        migrations.AlterUniqueTogether(
            name='disksharemount',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='disksharemount',
            name='asset',
        ),
        migrations.RemoveField(
            model_name='disksharemount',
            name='share',
        ),
        migrations.DeleteModel(
            name='DiskShare',
        ),
        migrations.DeleteModel(
            name='DiskShareMount',
        ),
    ]
