# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Preboot',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('description', models.TextField(default='', blank=True, verbose_name='description')),
            ],
            options={
                'verbose_name': 'preboot',
                'ordering': ('name',),
                'verbose_name_plural': 'preboots',
            },
        ),
        migrations.CreateModel(
            name='PrebootFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=255, verbose_name='name')),
                ('type', models.PositiveIntegerField(default=101, verbose_name='type', choices=[(1, 'kernel'), (2, 'initrd'), (41, 'boot_ipxe'), (42, 'kickstart'), (101, 'other')])),
                ('raw_config', models.TextField(blank=True, help_text='All newline characters will be converted to Unix \\n newlines. You can use {{variables}} in the body. Available variables: filename, filetype, mac, ip, hostname, venture and venture_role.', verbose_name='raw config')),
                ('description', models.TextField(default='', blank=True, verbose_name='description')),
            ],
            options={
                'verbose_name': 'preboot file',
                'verbose_name_plural': 'preboot files',
            },
        ),
        migrations.AddField(
            model_name='preboot',
            name='files',
            field=models.ManyToManyField(to='deployment.PrebootFile', blank=True, verbose_name='files'),
        ),
    ]
