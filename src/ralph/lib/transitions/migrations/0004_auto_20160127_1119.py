# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from ralph.admin.helpers import get_content_type_for_model


def migrate_transitionshistory(apps, schema_editor):
    TransitionsHistory = apps.get_model('transitions', 'TransitionsHistory')
    for item in TransitionsHistory.objects.all():
        model = apps.get_model(
            item.content_type.app_label, item.content_type.model
        )
        item.content_type_id = get_content_type_for_model(model).id
        item.save()


def unload_transitionshistory(apps, schema_editor):
    TransitionsHistory = apps.get_model('transitions', 'TransitionsHistory')
    BaseObject = apps.get_model('assets', 'BaseObject')
    for item in TransitionsHistory.objects.all():
        # Transitions are only for BackOfficeAsset and DataCenterAsset,
        # these models inherit from BaseObject
        item.content_type = BaseObject.objects.get(
            pk=item.object_id
        ).content_type
        item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('transitions', '0003_auto_20151202_1216'),
    ]

    operations = [
        migrations.RunPython(
            migrate_transitionshistory,
            reverse_code=unload_transitionshistory
        ),
    ]
