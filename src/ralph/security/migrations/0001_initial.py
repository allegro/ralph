# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityScan',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('last_scan_date', models.DateTimeField()),
                ('scan_status', models.PositiveIntegerField(choices=[(1, 'ok'), (2, 'fail'), (3, 'error')])),
                ('next_scan_date', models.DateTimeField()),
                ('details_url', models.URLField(blank=True, max_length=255)),
                ('rescan_url', models.URLField(verbose_name='Rescan url', blank=True)),
                ('base_object', models.ForeignKey(to='assets.BaseObject')),
                ('tags', taggit.managers.TaggableManager(verbose_name='Tags', to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Vulnerability',
            fields=[
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('name', models.CharField(verbose_name='name', max_length=1024)),
                ('patch_deadline', models.DateTimeField(null=True, blank=True)),
                ('risk', models.PositiveIntegerField(null=True, choices=[(1, 'low'), (2, 'medium'), (3, 'high')], blank=True)),
                ('external_vulnerability_id', models.IntegerField(null=True, unique=True, blank=True, help_text='Id of vulnerability from external system')),
                ('tags', taggit.managers.TaggableManager(verbose_name='Tags', to='taggit.Tag', through='taggit.TaggedItem', help_text='A comma-separated list of tags.', blank=True)),
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
