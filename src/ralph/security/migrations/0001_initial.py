# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('data_center', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityScan',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('last_scan_date', models.DateTimeField()),
                ('scan_status', models.PositiveIntegerField(choices=[(1, 'ok'), (2, 'fail'), (3, 'error')])),
                ('next_scan_date', models.DateTimeField()),
                ('details_url', models.URLField(max_length=255, blank=True)),
                ('rescan_url', models.URLField(verbose_name='Rescan url', blank=True)),
                ('asset', models.ForeignKey(null=True, to='data_center.DataCenterAsset')),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Vulnerability',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('patch_deadline', models.DateTimeField(null=True, blank=True)),
                ('risk', models.PositiveIntegerField(null=True, choices=[(1, 'low'), (2, 'medium'), (3, 'high')], blank=True)),
                ('external_vulnerability_id', models.IntegerField(null=True, unique=True, help_text='Id of vulnerability from external system', blank=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='securityscan',
            name='vulnerabilities',
            field=models.ManyToManyField(to='security.Vulnerability'),
        ),
    ]
