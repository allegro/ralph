# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields.json


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('content_type', models.ManyToManyField(to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='Transition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('source', django_extensions.db.fields.json.JSONField()),
                ('target', models.CharField(max_length=50)),
                ('actions', models.ManyToManyField(to='transitions.Action')),
            ],
        ),
        migrations.CreateModel(
            name='TransitionModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True, serialize=False)),
                ('field_name', models.CharField(max_length=50)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
        migrations.AddField(
            model_name='transition',
            name='model',
            field=models.ForeignKey(to='transitions.TransitionModel'),
        ),
        migrations.AlterUniqueTogether(
            name='transitionmodel',
            unique_together=set([('content_type', 'field_name')]),
        ),
        migrations.AlterUniqueTogether(
            name='transition',
            unique_together=set([('name', 'model')]),
        ),
    ]
