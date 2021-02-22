# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.models
from django.conf import settings
import django.db.models.deletion
import ralph.lib.transitions.fields


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_remove_ralphuser_gender'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('back_office', '0011_auto_20190517_1115'),
    ]

    operations = [
        migrations.CreateModel(
            name='Accessories',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('manufacturer', models.CharField(max_length=255, unique=True, help_text='Manufacturer of accessories')),
                ('accessories_type', models.CharField(max_length=255, unique=True, help_text='Type of accessories')),
                ('accessories_name', models.CharField(max_length=255, unique=True, help_text='Name of accessories')),
                ('product_number', models.CharField(max_length=255, unique=True, help_text='Number of accessories')),
                ('status', ralph.lib.transitions.fields.TransitionField(default=1, choices=[(1, 'new'), (2, 'in progress'), (3, 'lost'), (4, 'damaged'), (5, 'in use'), (6, 'free'), (7, 'return in progress'), (8, 'liquidated'), (9, 'reserved')], help_text='Accessories status')),
                ('number_bought', models.IntegerField(verbose_name='number of purchased items')),
                ('owner', models.ForeignKey(blank=True, null=True, help_text='Owner of the accessories', related_name='+', on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('region', models.ForeignKey(to='accounts.Region')),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
        migrations.CreateModel(
            name='AccessoriesUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('quantity', models.PositiveIntegerField(default=1)),
                ('accessories', models.ForeignKey(to='accessories.Accessories')),
                ('user', models.ForeignKey(related_name='user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='accessories',
            name='user',
            field=models.ManyToManyField(related_name='_accessories_user_+', to=settings.AUTH_USER_MODEL, through='accessories.AccessoriesUser'),
        ),
        migrations.AddField(
            model_name='accessories',
            name='warehouse',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='back_office.Warehouse'),
        ),
        migrations.AlterUniqueTogether(
            name='accessoriesuser',
            unique_together=set([('accessories', 'user')]),
        ),
    ]
