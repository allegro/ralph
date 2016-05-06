# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_region_country'),
        ('assets', '0015_auto_20160425_1335'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigurationClass',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('name', models.CharField(max_length=255, help_text='class name (ex. file name in puppet)', validators=[django.core.validators.RegexValidator(regex='\\w+')], verbose_name='name')),
                ('path', models.TextField(blank=True, verbose_name='path', default='', editable=False, help_text='path is constructed from names of modules in hierarchy')),
            ],
            options={
                'verbose_name': 'configuration class',
                'ordering': ('path',),
            },
        ),
        migrations.CreateModel(
            name='ConfigurationModule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('name', models.CharField(max_length=255, help_text='module name (ex. directory name in puppet)', validators=[django.core.validators.RegexValidator(regex='\\w+')], verbose_name='name')),
                ('path', models.TextField(blank=True, verbose_name='path', default='', editable=False, help_text='path is constructed from names of modules in hierarchy')),
                ('lft', models.PositiveIntegerField(db_index=True, editable=False)),
                ('rght', models.PositiveIntegerField(db_index=True, editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(db_index=True, editable=False)),
                ('parent', mptt.fields.TreeForeignKey(default=None, blank=True, verbose_name='parent module', to='assets.ConfigurationModule', null=True, related_name='children_modules')),
                ('support_team', models.ForeignKey(default=None, blank=True, verbose_name='team', null=True, on_delete=django.db.models.deletion.SET_NULL, to='accounts.Team')),
            ],
            options={
                'verbose_name': 'configuration module',
                'ordering': ('parent__name', 'name'),
            },
        ),
        migrations.AddField(
            model_name='configurationclass',
            name='module',
            field=models.ForeignKey(to='assets.ConfigurationModule', related_name='configuration_classes'),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='configuration_path',
            field=models.ForeignKey(blank=True, verbose_name='configuration path', help_text='path to configuration for this object, for example path to puppet class', null=True, to='assets.ConfigurationClass'),
        ),
        migrations.AlterUniqueTogether(
            name='configurationmodule',
            unique_together=set([('parent', 'name')]),
        ),
        migrations.AlterUniqueTogether(
            name='configurationclass',
            unique_together=set([('module', 'name')]),
        ),
    ]
