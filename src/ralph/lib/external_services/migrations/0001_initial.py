# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid
import django_extensions.db.fields.json
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
                ('id', models.UUIDField(serialize=False, default=uuid.uuid4, primary_key=True, editable=False)),
                ('user', ralph.lib.mixins.fields.NullableCharField(max_length=200, blank=True, null=True)),
                ('service_name', models.CharField(max_length=200)),
                ('params', django_extensions.db.fields.json.JSONField()),
                ('status', models.PositiveIntegerField(choices=[(1, 'queued'), (2, 'finished'), (3, 'failed'), (4, 'started')], default=1, verbose_name='job status')),
            ],
        ),
    ]
