# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ralph.reports.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReportLanguage',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReportTemplate',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now_add=True, verbose_name='last modified')),
                ('template', models.FileField(upload_to=ralph.reports.models.get_report_file_path)),
                ('default', models.BooleanField()),
                ('language', models.ForeignKey(to='reports.ReportLanguage')),
                ('report', models.ForeignKey(to='reports.Report', related_name='templates')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='reporttemplate',
            unique_together=set([('language', 'report')]),
        ),
    ]
