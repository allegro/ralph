# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0005_assetholder'),
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecurityScan',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('last_scan_date', models.DateTimeField()),
                ('scan_status', models.PositiveIntegerField(choices=[(1, 'ok'), (2, 'fail'), (3, 'error')])),
                ('next_scan_date', models.DateTimeField()),
                ('details_url', models.URLField(max_length=255, blank=True)),
                ('rescan_url', models.URLField(verbose_name='Rescan url', blank=True)),
                ('asset', models.ForeignKey(null=True, to='assets.BaseObject')),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', blank=True, through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Vulnerability',
            fields=[
                ('id', models.AutoField(auto_created=True, verbose_name='ID', primary_key=True, serialize=False)),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('patch_deadline', models.DateTimeField(null=True, blank=True)),
                ('risk', models.PositiveIntegerField(choices=[(1, 'low'), (2, 'medium'), (3, 'high')])),
                ('external_vulnerability_id', models.IntegerField(unique=True, null=True, help_text='Id of vulnerability from external system', blank=True)),
                ('tags', taggit.managers.TaggableManager(to='taggit.Tag', blank=True, through='taggit.TaggedItem', help_text='A comma-separated list of tags.', verbose_name='Tags')),
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
