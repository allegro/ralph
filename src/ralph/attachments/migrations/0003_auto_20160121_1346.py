# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

from ralph.admin.helpers import get_content_type_for_model


def migrate_attachment_item(apps, schema_editor):
    AttachmentItem = apps.get_model("attachments", "AttachmentItem")
    for item in AttachmentItem.objects.all():
        model = apps.get_model(item.content_type.app_label, item.content_type.model)
        item.content_type_id = get_content_type_for_model(model).id
        item.save()


def unload_migrate_attachment_item(apps, schema_editor):
    AttachmentItem = apps.get_model("attachments", "AttachmentItem")
    BaseObject = apps.get_model("assets", "BaseObject")
    ContentType = apps.get_model("contenttypes", "ContentType")
    bo_content_type = ContentType.objects.get_for_model(BaseObject)
    for item in AttachmentItem.objects.filter(content_type=bo_content_type):
        content_type = BaseObject.objects.get(pk=item.object_id).content_type
        item.content_type = content_type
        item.save()


class Migration(migrations.Migration):
    dependencies = [
        ("attachments", "0002_auto_20151125_1354"),
        ("back_office", "0003_auto_20151204_0758"),
        ("data_center", "0004_auto_20151204_0758"),
        ("domains", "0002_auto_20151125_1354"),
        ("licences", "0002_auto_20151204_1325"),
        ("supports", "0005_auto_20160105_1222"),
    ]

    operations = [
        migrations.RunPython(
            migrate_attachment_item, reverse_code=unload_migrate_attachment_item
        ),
    ]
