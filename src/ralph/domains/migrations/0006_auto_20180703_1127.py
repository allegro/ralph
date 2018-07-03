# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import multiselectfield.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0005_auto_20170523_1214'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalServices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
            ],
        ),
        migrations.AddField(
            model_name='domain',
            name='additional_services',
            field=multiselectfield.db.fields.MultiSelectField(max_length=34, null=True, choices=[('None', 'None'), ('Masking', 'Masking'), ('Backorder', 'Backorder'), ('Acquisition', 'Acquisition')], blank=True),
        ),
    ]
