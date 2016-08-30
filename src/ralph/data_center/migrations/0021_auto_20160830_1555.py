# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_center', '0020_auto_20160830_1402'),
    ]

    operations = [
        migrations.AddField(
            model_name='vip',
            name='ip',
            field=models.GenericIPAddressField(null=True, verbose_name='IP address'),
        ),
        migrations.AlterUniqueTogether(
            name='vip',
            unique_together=set([('ip', 'port', 'protocol')]),
        ),
    ]
