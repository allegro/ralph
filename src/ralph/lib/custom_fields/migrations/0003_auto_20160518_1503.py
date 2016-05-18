# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('custom_fields', '0002_auto_20160515_1742'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customfield',
            name='attribute_name',
            field=models.SlugField(editable=False, unique=True, help_text="field name used in API. It's slugged name of the field", max_length=255),
        ),
        migrations.AlterField(
            model_name='customfield',
            name='type',
            field=models.PositiveIntegerField(default=1, choices=[(1, 'string'), (2, 'integer'), (3, 'date'), (4, 'url'), (5, 'choice list')]),
        ),
        migrations.AlterField(
            model_name='customfieldvalue',
            name='custom_field',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, verbose_name='key', to='custom_fields.CustomField'),
        ),
    ]
