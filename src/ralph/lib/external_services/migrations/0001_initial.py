# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import uuid

import django_extensions.db.fields.json
from django.db import migrations, models

import ralph.lib.mixins.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Job',
            fields=[
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('id', models.UUIDField(serialize=False, primary_key=True, default=uuid.uuid4, editable=False)),
                ('username', ralph.lib.mixins.fields.NullableCharField(max_length=200, null=True, blank=True)),
                ('service_name', models.CharField(max_length=200)),
                ('_dumped_params', django_extensions.db.fields.json.JSONField()),
                ('status', models.PositiveIntegerField(choices=[(1, 'queued'), (2, 'finished'), (3, 'failed'), (4, 'started')], verbose_name='job status', default=1)),
            ],
        ),
    ]
