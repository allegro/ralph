# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('data_importer', '0002_auto_20151125_1354'),
    ]

    operations = [
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('object_pk', models.IntegerField(db_index=True)),
                ('result', django_extensions.db.fields.json.JSONField()),
                ('errors', django_extensions.db.fields.json.JSONField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('old', models.ForeignKey(null=True, to='data_importer.ImportedObjects')),
            ],
            options={
                'abstract': False,
                'ordering': ('-modified', '-created'),
            },
        ),
        migrations.CreateModel(
            name='Run',
            fields=[
                ('id', models.AutoField(serialize=False, auto_created=True, primary_key=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('checked_count', models.PositiveIntegerField(default=0)),
                ('invalid_count', models.PositiveIntegerField(default=0)),
                ('valid_count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'abstract': False,
                'ordering': ('-modified', '-created'),
            },
        ),
        migrations.AddField(
            model_name='result',
            name='run',
            field=models.ForeignKey(to='cross_validator.Run'),
        ),
    ]
