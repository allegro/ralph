# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import ralph.lib.mixins.models
import django.db.models.deletion
import ralph.lib.transitions.fields
import mptt.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0032_auto_20200909_1012'),
        ('accounts', '0006_remove_ralphuser_gender'),
        ('back_office', '0012_auto_20210318_1230'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accessory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('accessory_name', models.CharField(max_length=255, unique=True, help_text='Accessory name')),
                ('product_number', models.CharField(max_length=255, unique=True, help_text='Number of accessories')),
                ('status', ralph.lib.transitions.fields.TransitionField(default=1, choices=[(1, 'new'), (2, 'in progress'), (3, 'lost'), (4, 'damaged'), (5, 'in use'), (6, 'free'), (7, 'return in progress'), (8, 'liquidated'), (9, 'reserved')], help_text='Accessory status')),
                ('number_bought', models.IntegerField(verbose_name='number of purchased items')),
                ('category', mptt.fields.TreeForeignKey(null=True, related_name='+', to='assets.Category')),
                ('manufacturer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='assets.Manufacturer')),
                ('owner', models.ForeignKey(blank=True, null=True, help_text='Accessory owner', related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('region', models.ForeignKey(to='accounts.Region')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='AccessoryUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('accessory', models.ForeignKey(to='accessories.Accessory')),
                ('user', models.ForeignKey(related_name='user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='accessory',
            name='user',
            field=models.ManyToManyField(related_name='_accessory_user_+', to=settings.AUTH_USER_MODEL, through='accessories.AccessoryUser'),
        ),
        migrations.AddField(
            model_name='accessory',
            name='warehouse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='back_office.Warehouse'),
        ),
        migrations.AlterUniqueTogether(
            name='accessoryuser',
            unique_together=set([('accessory', 'user')]),
        ),
    ]
