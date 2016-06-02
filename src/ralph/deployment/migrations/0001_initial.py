# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.deployment.models


class Migration(migrations.Migration):

    dependencies = [
        ('transitions', '0006_auto_20160401_0842'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Preboot',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
                ('description', models.TextField(default='', verbose_name='description', blank=True)),
                ('used_counter', models.PositiveIntegerField(default=0, editable=False)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'preboot',
                'verbose_name_plural': 'preboots',
            },
        ),
        migrations.CreateModel(
            name='PrebootItem',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', auto_created=True, primary_key=True)),
                ('name', models.CharField(verbose_name='name', unique=True, max_length=255)),
                ('description', models.TextField(default='', verbose_name='description', blank=True)),
            ],
            options={
                'abstract': False,
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('transitions.transitionjob',),
        ),
        migrations.CreateModel(
            name='PrebootConfiguration',
            fields=[
                ('prebootitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, serialize=False, to='deployment.PrebootItem', primary_key=True)),
                ('type', models.PositiveIntegerField(default=41, verbose_name='type', choices=[(41, 'ipxe'), (42, 'kickstart')])),
                ('configuration', models.TextField(verbose_name='configuration', help_text='All newline characters will be converted to Unix \\n newlines. You can use {{variables}} in the body. Available variables: filename, filetype, mac, ip, hostname, venture and venture_role.', blank=True)),
            ],
            options={
                'verbose_name': 'preboot configuration',
                'verbose_name_plural': 'preboot configuration',
            },
            bases=('deployment.prebootitem',),
        ),
        migrations.CreateModel(
            name='PrebootFile',
            fields=[
                ('prebootitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, serialize=False, to='deployment.PrebootItem', primary_key=True)),
                ('type', models.PositiveIntegerField(default=1, verbose_name='type', choices=[(1, 'kernel'), (2, 'initrd')])),
                ('file', models.FileField(null=True, default=None, verbose_name='file', upload_to=ralph.deployment.models.preboot_file_name, blank=True)),
            ],
            options={
                'verbose_name': 'preboot file',
                'verbose_name_plural': 'preboot files',
            },
            bases=('deployment.prebootitem',),
        ),
        migrations.AddField(
            model_name='prebootitem',
            name='content_type',
            field=models.ForeignKey(blank=True, null=True, to='contenttypes.ContentType'),
        ),
        migrations.AddField(
            model_name='preboot',
            name='items',
            field=models.ManyToManyField(to='deployment.PrebootItem', verbose_name='files', blank=True),
        ),
    ]
