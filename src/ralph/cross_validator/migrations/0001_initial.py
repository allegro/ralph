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
            name='CrossValidationResult',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('object_pk', models.IntegerField(db_index=True)),
                ('diff', django_extensions.db.fields.json.JSONField()),
                ('errors', django_extensions.db.fields.json.JSONField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('old', models.ForeignKey(to='data_importer.ImportedObjects', null=True)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CrossValidationRun',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, serialize=False, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('checked_count', models.PositiveIntegerField(default=0)),
                ('invalid_count', models.PositiveIntegerField(default=0)),
                ('valid_count', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='crossvalidationresult',
            name='run',
            field=models.ForeignKey(to='cross_validator.CrossValidationRun'),
        ),
    ]
