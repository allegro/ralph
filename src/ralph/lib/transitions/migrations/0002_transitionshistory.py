# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('transitions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransitionsHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('object_id', models.IntegerField(db_index=True)),
                ('kwargs', django_extensions.db.fields.json.JSONField()),
                ('actions', django_extensions.db.fields.json.JSONField()),
                ('attachment', models.ForeignKey(to='attachments.Attachment', null=True, blank=True)),
                ('logged_user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('transition', models.ForeignKey(to='transitions.Transition')),
            ],
            options={
                'abstract': False,
                'ordering': ('-modified', '-created'),
            },
        ),
    ]
