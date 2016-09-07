# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domains', '0003_auto_20160823_0921'),
    ]

    operations = [
        migrations.AddField(
            model_name='domain',
            name='website_type',
            field=models.PositiveIntegerField(help_text='Type of website which domain refers to.', default=1, choices=[(1, 'None'), (2, 'Redirect'), (3, 'Direct')]),
        ),
        migrations.AddField(
            model_name='domain',
            name='website_url',
            field=models.URLField(max_length=255, blank=True, null=True, help_text='Website url which website type refers to.'),
        ),
    ]
