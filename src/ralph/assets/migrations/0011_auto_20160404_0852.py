# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import re
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0010_auto_20160405_1531'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ethernet',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, auto_created=True, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='date created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='last modified')),
                ('label', models.CharField(max_length=255, verbose_name='name')),
                ('mac', models.CharField(validators=[django.core.validators.RegexValidator(regex=re.compile('^\\s*([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}\\s*$', 32), message="'%(value)s' is not a valid MAC address.")], unique=True, verbose_name='MAC address', max_length=24)),
                ('speed', models.PositiveIntegerField(default=11, verbose_name='speed', choices=[(1, '10 Mbps'), (2, '100 Mbps'), (3, '1 Gbps'), (4, '10 Gbps'), (11, 'unknown speed')])),
                ('base_object', models.ForeignKey(related_name='ethernet', to='assets.BaseObject')),
                ('model', models.ForeignKey(blank=True, verbose_name='model', default=None, on_delete=django.db.models.deletion.SET_NULL, null=True, to='assets.ComponentModel')),
            ],
            options={
                'verbose_name_plural': 'ethernets',
                'ordering': ('base_object', 'mac'),
                'verbose_name': 'ethernet',
            },
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='created',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now, verbose_name='date created'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='genericcomponent',
            name='modified',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now, verbose_name='last modified'),
            preserve_default=False,
        ),
    ]
