# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0007_auto_20151118_0804'),
        ('supports', '0003_support_budget_info'),
    ]

    operations = [
        migrations.AddField(
            model_name='support',
            name='asset_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'back office'), (2, 'data center'), (3, 'part'), (4, 'all')], default=4),
        ),
        migrations.AddField(
            model_name='support',
            name='property_of',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, null=True, blank=True, to='assets.AssetHolder'),
        ),
        migrations.AlterField(
            model_name='support',
            name='contract_terms',
            field=models.TextField(blank=True),
        ),
    ]
