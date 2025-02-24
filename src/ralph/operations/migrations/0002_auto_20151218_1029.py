# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations

OPERATION_TYPES = (
    (1, "Change", []),
    (101, "Incident", []),
    (201, "Problem", []),
    (
        301,
        "Failure",
        [
            (
                302,
                "Hardware Failure",
                [
                    (303, "Disk", []),
                    (304, "Controller", []),
                    (305, "RAM", []),
                    (
                        306,
                        "Eth card",
                        [
                            (307, "Eth card 1Gb", []),
                            (308, "Eth card 10Gb", []),
                        ],
                    ),
                    (309, "Management Module", []),
                    (310, "Power supply", []),
                    (311, "Fan", []),
                    (312, "SFP", []),
                    (313, "Motherboard", []),
                    (314, "Firmware upgrade", []),
                    (315, "Backplane", []),
                ],
            )
        ],
    ),
)


def load_operation(model, obj_id, name, parent, children):
    obj = model.objects.create(
        id=obj_id,
        pk=obj_id,
        name=name,
        parent=parent,
        **{"lft": 0, "rght": 0, "level": 0, "tree_id": 0},
    )
    for child_id, child_name, child_children in children:
        load_operation(model, child_id, child_name, obj, child_children)


def load_initial_data(apps, schema_editor):
    OperationType = apps.get_model("operations", "OperationType")
    for op_id, op_name, op_children in OPERATION_TYPES:
        load_operation(OperationType, op_id, op_name, None, op_children)


def unload_initial_data(apps, schema_editor):
    OperationType = apps.get_model("operations", "OperationType")
    OperationType.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(load_initial_data, reverse_code=unload_initial_data),
    ]
