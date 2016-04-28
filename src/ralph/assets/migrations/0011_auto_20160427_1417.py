# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import mptt.fields
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_region_country'),
        ('assets', '0010_auto_20160405_1531'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfigurationClass',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('name', models.CharField(help_text='class name (ex. file name in puppet)', validators=[django.core.validators.RegexValidator(regex='\\w+')], max_length=255, verbose_name='name')),
                ('path', models.TextField(help_text='path is constructed from names of modules in hierarchy', default='', editable=False, verbose_name='path', blank=True)),
            ],
            options={
                'ordering': ('path',),
                'verbose_name': 'configuration class',
            },
        ),
        migrations.CreateModel(
            name='ConfigurationModule',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('name', models.CharField(help_text='module name (ex. directory name in puppet)', validators=[django.core.validators.RegexValidator(regex='\\w+')], max_length=255, verbose_name='name')),
                ('path', models.TextField(help_text='path is constructed from names of modules in hierarchy', default='', editable=False, verbose_name='path', blank=True)),
                ('lft', models.PositiveIntegerField(editable=False, db_index=True)),
                ('rght', models.PositiveIntegerField(editable=False, db_index=True)),
                ('tree_id', models.PositiveIntegerField(editable=False, db_index=True)),
                ('level', models.PositiveIntegerField(editable=False, db_index=True)),
                ('parent', mptt.fields.TreeForeignKey(verbose_name='parent venture', to='assets.ConfigurationModule', blank=True, related_name='children_modules', default=None, null=True)),
                ('support_team', models.ForeignKey(on_delete=django.db.models.deletion.SET_NULL, default=None, to='accounts.Team', verbose_name='team', blank=True, null=True)),
            ],
            options={
                'ordering': ('parent__name', 'name'),
                'verbose_name': 'configuration module',
            },
        ),
        migrations.AddField(
            model_name='configurationclass',
            name='module',
            field=models.ForeignKey(related_name='configuration_classes', to='assets.ConfigurationModule'),
        ),
        migrations.AddField(
            model_name='baseobject',
            name='configuration_path',
            field=models.ForeignKey(verbose_name='configuration class', help_text='path to configuration for this object, for example path to puppet class', to='assets.ConfigurationClass', blank=True, null=True),
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
