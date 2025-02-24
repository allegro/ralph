# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('external_services', '__first__'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('transitions', '0004_auto_20160127_1119'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransitionJob',
            fields=[
                ('job_ptr', models.OneToOneField(parent_link=True, serialize=False, auto_created=True, to='external_services.Job', primary_key=True, on_delete=django.db.models.deletion.CASCADE)),
                ('object_id', models.CharField(max_length=200)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
                'ordering': ('-modified', '-created'),
            },
            bases=('external_services.job',),
        ),
        migrations.CreateModel(
            name='TransitionJobAction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('action_name', models.CharField(max_length=50)),
                ('status', models.PositiveIntegerField(default=1, verbose_name='transition action status', choices=[(1, 'started'), (2, 'finished'), (3, 'failed')])),
                ('transition_job', models.ForeignKey(related_name='transition_job_actions', to='transitions.TransitionJob', on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={
                'abstract': False,
                'ordering': ('-modified', '-created'),
            },
        ),
        migrations.AddField(
            model_name='transition',
            name='async_service_name',
            field=models.CharField(default='ASYNC_TRANSITIONS', blank=True, help_text='Name of asynchronous (internal) service to run this transition. Fill this field only if you want to run this transition in the background.', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='transition',
            name='run_asynchronously',
            field=models.BooleanField(default=False, help_text='Run this transition in the background (this could be enforced if you choose at least one asynchronous action)'),
        ),
        migrations.AddField(
            model_name='transitionjob',
            name='transition',
            field=models.ForeignKey(to='transitions.Transition', on_delete=django.db.models.deletion.CASCADE),
        ),
    ]
