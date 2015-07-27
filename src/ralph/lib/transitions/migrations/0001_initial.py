# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='TransitionConfigModel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('name', models.CharField(verbose_name='name', max_length=50)),
                ('field_name', models.CharField(verbose_name='field name', max_length=50)),
                ('source', models.CharField(verbose_name='source', default='*', max_length=50)),
                ('target', models.CharField(verbose_name='target', max_length=50)),
                ('actions', models.CharField(verbose_name='actions', max_length=150)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
        ),
    ]
