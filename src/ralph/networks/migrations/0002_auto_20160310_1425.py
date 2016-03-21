# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.fields
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('networks', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='network',
            name='terminators',
        ),
        migrations.DeleteModel(
            name='NetworkTerminator',
        ),
        migrations.RenameField(
            model_name='networkenvironment',
            old_name='next_server',
            new_name='dhcp_next_server',
        ),
        migrations.AlterField(
            model_name='ipaddress',
            name='address',
            field=models.GenericIPAddressField(unique=True, default=None, help_text='Presented as string.', verbose_name='IP address'),
        ),
        migrations.AlterField(
            model_name='ipaddress',
            name='hostname',
            field=ralph.lib.mixins.fields.NullableCharField(default=None, null=True, max_length=255, blank=True, verbose_name='Hostname'),
        ),
        migrations.AlterField(
            model_name='network',
            name='dhcp_broadcast',
            field=models.BooleanField(default=True, verbose_name='Broadcast in DHCP configuration', db_index=True),
        ),
        migrations.AlterField(
            model_name='network',
            name='kind',
            field=models.ForeignKey(to='networks.NetworkKind', on_delete=django.db.models.deletion.SET_NULL, null=True, verbose_name='network kind', blank=True),
        ),
        migrations.AlterField(
            model_name='network',
            name='max_ip',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=39, verbose_name='largest IP number', editable=False),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='network',
            name='min_ip',
            field=models.DecimalField(decimal_places=0, default=0, max_digits=39, verbose_name='smallest IP number', editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='network',
            name='terminators',
            field=models.ManyToManyField(to='assets.BaseObject', verbose_name='network terminators', blank=True),
        ),
        migrations.AlterField(
            model_name='networkenvironment',
            name='domain',
            field=ralph.lib.mixins.fields.NullableCharField(null=True, max_length=255, blank=True, verbose_name='domain'),
        ),
    ]
