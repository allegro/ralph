# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('name', models.CharField(unique=True, max_length=255)),
                ('attribute_name', models.SlugField(unique=True, max_length=255, editable=False)),
                ('type', models.PositiveIntegerField(choices=[(1, 'string'), (2, 'integer'), (3, 'date'), (4, 'boolean'), (5, 'url'), (6, 'choice list'), (7, 'multi-choice list')], default=1)),
                ('choices', models.CharField(verbose_name='choices', max_length=1024, help_text='available choices for `choices list` separated by |', null=True, blank=True)),
                ('default_value', models.CharField(max_length=1000, help_text='for boolean use "true" or "false"')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CustomFieldValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, primary_key=True, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('value', models.CharField(max_length=1000)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('custom_field', models.ForeignKey(to='custom_fields.CustomField')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='customfieldvalue',
            unique_together=set([('custom_field', 'content_type', 'object_id')]),
        ),
    ]
