# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import ralph.lib.mixins.models
import dj.choices.fields
from django.conf import settings
import ralph.access_cards.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessCard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', primary_key=True, serialize=False, auto_created=True)),
                ('created', models.DateTimeField(verbose_name='date created', auto_now_add=True)),
                ('modified', models.DateTimeField(verbose_name='last modified', auto_now=True)),
                ('visual_number', models.CharField(max_length=256, help_text='Number visible on the access card')),
                ('system_number', models.CharField(max_length=256, help_text='Internal number in the access system')),
                ('issue_date', models.DateField(blank=True, null=True, help_text='Date of issue to the User')),
                ('notes', models.TextField(blank=True, null=True, help_text='Optional notes')),
                ('status', dj.choices.fields.ChoiceField(default=1, choices=ralph.access_cards.models.AccessCardStatus, help_text='Access card status')),
                ('owner', models.ForeignKey(blank=True, null=True, help_text='Owner of the card', related_name='owned_access_cards', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(blank=True, null=True, help_text='User of the card', related_name='used_access_cards', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-modified', '-created'),
                'abstract': False,
            },
            bases=(ralph.lib.mixins.models.AdminAbsoluteUrlMixin, models.Model),
        ),
    ]
