# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.transitions.fields
import ralph.lib.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('tests', '0005_bar_foos'),
    ]

    operations = [
        migrations.CreateModel(
            name='AsyncOrder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', auto_created=True, primary_key=True, serialize=False)),
                ('status', ralph.lib.transitions.fields.TransitionField(choices=[(1, 'new'), (2, 'to_send'), (3, 'sended')], default=1)),
                ('name', models.CharField(max_length=100)),
                ('counter', models.PositiveSmallIntegerField(default=1)),
                ('username', models.CharField(blank=True, max_length=100, null=True)),
                ('foo', models.ForeignKey(blank=True, to='tests.Foo', null=True)),
            ],
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
    ]
