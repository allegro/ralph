# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('external_services', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('transitions', '0004_auto_20160127_1119'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransitionJob',
            fields=[
                ('job_ptr', models.OneToOneField(serialize=False, parent_link=True, auto_created=True, primary_key=True, to='external_services.Job')),
                ('object_id', models.CharField(max_length=200)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=('external_services.job',),
        ),
        migrations.CreateModel(
            name='TransitionJobAction',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('action_name', models.CharField(max_length=50)),
                ('status', models.PositiveIntegerField(choices=[(1, 'started'), (2, 'finished'), (3, 'failed')], default=1, verbose_name='transition action status')),
                ('transition_job', models.ForeignKey(to='transitions.TransitionJob', on_delete=django.db.models.deletion.PROTECT, related_name='transition_job_actions')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='transition',
            name='async_service_name',
            field=models.CharField(max_length=100, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='transitionjob',
            name='transition',
            field=models.ForeignKey(to='transitions.Transition'),
        ),
    ]
