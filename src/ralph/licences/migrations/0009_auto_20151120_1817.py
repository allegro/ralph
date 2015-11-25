# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licences', '0008_licence_office_infrastructure'),
    ]

    operations = [
        migrations.AlterField(
            model_name='baseobjectlicence',
            name='base_object',
            field=models.ForeignKey(verbose_name='Asset', related_name='licences', to='assets.BaseObject'),
        ),
    ]
