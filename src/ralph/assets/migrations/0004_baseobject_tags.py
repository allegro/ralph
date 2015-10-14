# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('taggit', '0002_auto_20150616_2121'),
        ('assets', '0003_auto_20150911_1254'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseobject',
            name='tags',
            field=taggit.managers.TaggableManager(through='taggit.TaggedItem', to='taggit.Tag', verbose_name='Tags', blank=True, help_text='A comma-separated list of tags.'),
        ),
    ]
