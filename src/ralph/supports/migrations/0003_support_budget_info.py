# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0006_auto_20151110_1448'),
        ('supports', '0002_support_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='support',
            name='budget_info',
            field=models.ForeignKey(null=True, to='assets.BudgetInfo', blank=True, on_delete=django.db.models.deletion.PROTECT, default=None),
        ),
    ]
