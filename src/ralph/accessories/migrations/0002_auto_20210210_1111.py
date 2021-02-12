# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accessories', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='accessories',
            name='user',
        ),
        migrations.AddField(
            model_name='accessories',
            name='user',
            field=models.ManyToManyField(related_name='_accessories_user_+', to=settings.AUTH_USER_MODEL, through='accessories.AccessoriesUser'),
        ),
        migrations.AlterField(
            model_name='accessoriesuser',
            name='user',
            field=models.ForeignKey(related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
