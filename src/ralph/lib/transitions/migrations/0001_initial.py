# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
import django_extensions.db.fields.json
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('content_type', models.ManyToManyField(to='contenttypes.ContentType')),
            ],
        ),
        migrations.CreateModel(
            name='Transition',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('source', django_extensions.db.fields.json.JSONField()),
                ('target', models.CharField(max_length=50)),
                ('actions', models.ManyToManyField(to='transitions.Action')),
            ],
        ),
        migrations.CreateModel(
            name='TransitionModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('field_name', models.CharField(max_length=50)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='TransitionsHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('transition_name', models.CharField(max_length=255)),
                ('source', models.CharField(blank=True, null=True, max_length=50)),
                ('target', models.CharField(blank=True, null=True, max_length=50)),
                ('object_id', models.IntegerField(db_index=True)),
                ('kwargs', django_extensions.db.fields.json.JSONField()),
                ('actions', django_extensions.db.fields.json.JSONField()),
                ('attachment', models.ForeignKey(to='attachments.Attachment', blank=True, null=True, on_delete=django.db.models.deletion.CASCADE)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType', on_delete=django.db.models.deletion.CASCADE)),
                ('logged_user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='transition',
            name='model',
            field=models.ForeignKey(to='transitions.TransitionModel', on_delete=django.db.models.deletion.CASCADE),
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
