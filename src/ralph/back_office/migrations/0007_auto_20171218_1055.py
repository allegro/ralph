# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models

from ralph.lib.transitions.models import TransitionModel as _TransitionModel


NAME = 'Accept by the current user'


def add_empty_transition_for_user_acceptance(apps, schema_editor):
    Transition = apps.get_model('transitions', 'Transition')
    TransitionModel = apps.get_model('transitions', 'TransitionModel')
    BackOfficeAsset = apps.get_model('back_office', 'BackOfficeAsset')
    transition_id = settings.ACCEPT_ASSETS_FOR_CURRENT_USER_CONFIG['TRANSITION_ID']  # noqa
    transition_model = _TransitionModel.get_for_field(
        model=BackOfficeAsset, field_name='status'
    )
    transition = Transition(
        id=transition_id,
        name=NAME,
        model=TransitionModel.objects.get(id=transition_model.id)
    )
    transition.save()


def delete_transition(apps, schema_editor):
    Transition = apps.get_model('transitions', 'Transition')
    Transition.objects.filter(name=NAME).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('back_office', '0006_auto_20160902_1238'),
        ('transitions', '0008_auto_20171211_1300'),
    ]

    operations = [
        migrations.RunPython(
            add_empty_transition_for_user_acceptance,
            reverse_code=delete_transition
        )
    ]
