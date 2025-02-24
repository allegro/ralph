# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('attribute_name', models.SlugField(unique=True, editable=False, help_text="field name used in API. It's slugged name of the field", max_length=255)),
                ('type', models.PositiveIntegerField(default=1, choices=[(1, 'string'), (2, 'integer'), (3, 'date'), (4, 'url'), (5, 'choice list')])),
                ('choices', models.CharField(help_text='available choices for `choices list` separated by |', verbose_name='choices', blank=True, null=True, max_length=1024)),
                ('default_value', models.CharField(default='', help_text='for boolean use "true" or "false"', blank=True, null=True, max_length=1000)),
            ],
            options={
                'abstract': False,
                'ordering': ('-modified', '-created'),
            },
        ),
        migrations.CreateModel(
            name='CustomFieldValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('value', models.CharField(max_length=1000)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.CASCADE)),
                ('custom_field', models.ForeignKey(verbose_name='key', on_delete=django.db.models.deletion.PROTECT, to='custom_fields.CustomField')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='customfieldvalue',
            unique_together=set([('custom_field', 'content_type', 'object_id')]),
        ),
    ]
