# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def migrate_visualization(apps, schema_editor):
    DataCenter = apps.get_model("data_center", "DataCenter")
    ServerRoom = apps.get_model("data_center", "ServerRoom")

    data_centers = DataCenter.objects.all()

    for data_center in data_centers:
        server_rooms = ServerRoom.objects.filter(data_center__id=data_center.id)
        for server_room in server_rooms:
            server_room.visualization_cols_num = data_center.visualization_cols_num
            server_room.visualization_rows_num = data_center.visualization_rows_num
            server_room.save()


def migrate_visualization_rev(apps, schema_editor):
    DataCenter = apps.get_model("data_center", "DataCenter")
    ServerRoom = apps.get_model("data_center", "ServerRoom")
    data_centers = DataCenter.objects.all()
    print(data_centers.first().visualization_cols_num)
    for data_center in data_centers:
        server_room = ServerRoom.objects.filter(data_center__id=data_center.id)
        if server_room:
            data_center.visualization_cols_num = server_room[0].visualization_cols_num
            data_center.visualization_rows_num = server_room[0].visualization_rows_num
            data_center.save()


class Migration(migrations.Migration):
    dependencies = [
        ("data_center", "0009_auto_20160419_1003"),
    ]

    operations = [
        migrations.AddField(
            model_name="serverroom",
            name="visualization_cols_num",
            field=models.PositiveIntegerField(
                verbose_name="visualization grid columns number", default=20
            ),
        ),
        migrations.AddField(
            model_name="serverroom",
            name="visualization_rows_num",
            field=models.PositiveIntegerField(
                verbose_name="visualization grid rows number", default=20
            ),
        ),
        migrations.RunPython(migrate_visualization, migrate_visualization_rev),
        migrations.RemoveField(
            model_name="datacenter",
            name="visualization_cols_num",
        ),
        migrations.RemoveField(
            model_name="datacenter",
            name="visualization_rows_num",
        ),
    ]
