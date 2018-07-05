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
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
            ],
        ),
        migrations.AddField(
            model_name='domain',
            name='additional_services',
            field=multiselectfield.db.fields.MultiSelectField(blank=True, max_length=29, null=True, choices=[('Masking', 'Masking'), ('Backorder', 'Backorder'), ('Acquisition', 'Acquisition')]),
        ),
    ]
