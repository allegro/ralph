# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('assets', '0005_assetholder'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityScan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('last_scan_date', models.DateTimeField()),
                ('scan_status', models.PositiveIntegerField(choices=[(1, 'ok'), (2, 'fail'), (3, 'error')])),
                ('next_scan_date', models.DateTimeField()),
                ('details_url', models.URLField(blank=True, max_length=255)),
                ('rescan_url', models.URLField(blank=True, verbose_name='Rescan url')),
                ('asset', models.ForeignKey(null=True, to='assets.BaseObject')),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags', to='taggit.Tag', through='taggit.TaggedItem')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Vulnerability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, verbose_name='ID', serialize=False)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('patch_deadline', models.DateTimeField(blank=True, null=True)),
                ('risk', models.PositiveIntegerField(choices=[(1, 'low'), (2, 'medium'), (3, 'high')])),
                ('external_vulnerability_id', models.IntegerField(blank=True, help_text='Id of vulnerability from external system', null=True, unique=True)),
                ('security_scans', models.ManyToManyField(to='security.SecurityScan')),
                ('tags', taggit.managers.TaggableManager(blank=True, help_text='A comma-separated list of tags.', verbose_name='Tags', to='taggit.Tag', through='taggit.TaggedItem')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
