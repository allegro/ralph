# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0004_baseobject_tags'),
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityScan',
            fields=[
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('last_scan_date', models.DateTimeField()),
                ('scan_status', models.PositiveIntegerField(choices=[(1, 'ok'), (2, 'fail'), (3, 'error')])),
                ('next_scan_date', models.DateTimeField()),
                ('details_url', models.URLField(max_length=255, blank=True)),
                ('rescan_url', models.URLField(blank=True, verbose_name='Rescan url')),
                ('asset', models.OneToOneField(serialize=False, primary_key=True, to='assets.BaseObject')),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', to='taggit.Tag', verbose_name='Tags', through='taggit.TaggedItem', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Vulnerability',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, primary_key=True, verbose_name='ID')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('name', models.CharField(max_length=511, verbose_name='name')),
                ('days_to_patch', models.PositiveIntegerField()),
                ('risk', models.PositiveIntegerField(choices=[(1, 'low'), (2, 'medium'), (3, 'high')])),
                ('compliance_patching_policy', models.CharField(max_length=100, blank=True)),
                ('external_vulnerability_id', models.IntegerField(help_text='Id of vulnerability from external system', blank=True, unique=True)),
                ('security_scan', models.ForeignKey(to='security.SecurityScan')),
                ('tags', taggit.managers.TaggableManager(help_text='A comma-separated list of tags.', to='taggit.Tag', verbose_name='Tags', through='taggit.TaggedItem', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
