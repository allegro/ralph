# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0006_auto_20151110_0949'),
        ('licences', '0007_licence_budget_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='licence',
            name='office_infrastructure',
            field=models.ForeignKey(blank=True, null=True, to='back_office.OfficeInfrastructure'),
        ),
    ]
