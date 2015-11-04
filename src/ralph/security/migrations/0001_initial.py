# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('data_center', '0003_fix_ip_int'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityScan',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('last_scan_date', models.DateTimeField()),
                ('scan_status', models.PositiveIntegerField(choices=[(1, 'ok'), (2, 'fail'), (3, 'error')])),
                ('next_scan_date', models.DateTimeField()),
                ('details_url', models.URLField(max_length=255, blank=True)),
                ('rescan_url', models.URLField(blank=True, verbose_name='Rescan url')),
                ('asset', models.ForeignKey(null=True, to='data_center.DataCenterAsset')),
                ('tags', taggit.managers.TaggableManager(blank=True, through='taggit.TaggedItem', verbose_name='Tags', help_text='A comma-separated list of tags.', to='taggit.Tag')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Vulnerability',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', serialize=False, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now_add=True)),
                ('name', models.CharField(max_length=255, verbose_name='name', unique=True)),
                ('patch_deadline', models.DateTimeField(blank=True, null=True)),
                ('risk', models.PositiveIntegerField(choices=[(1, 'low'), (2, 'medium'), (3, 'high')])),
                ('external_vulnerability_id', models.IntegerField(blank=True, null=True, unique=True, help_text='Id of vulnerability from external system')),
                ('tags', taggit.managers.TaggableManager(blank=True, through='taggit.TaggedItem', verbose_name='Tags', help_text='A comma-separated list of tags.', to='taggit.Tag')),
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
