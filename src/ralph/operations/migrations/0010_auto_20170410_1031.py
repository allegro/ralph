# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django.db.models.deletion
from dj.choices import Choices
from django.conf import settings
from django.db import migrations, models

from ralph.operations.models import OperationStatus


class OldOperationStatus(Choices):
    _ = Choices.Choice

    opened = _("open")
    in_progress = _("in progress")
    resolved = _("resolved")
    closed = _("closed")
    reopened = _("reopened")
    todo = _("todo")
    blocked = _("blocked")


def safe_convert_status(status_name):
    try:
        status_conf = settings.CHANGE_MGMT_OPERATION_STATUSES

        status_map = {
            OldOperationStatus.opened.raw: status_conf["OPENED"],
            OldOperationStatus.in_progress.raw: status_conf["IN_PROGRESS"],
            OldOperationStatus.resolved.raw: status_conf["RESOLVED"],
            OldOperationStatus.closed.raw: status_conf["CLOSED"],
            OldOperationStatus.reopened.raw: status_conf["REOPENED"],
            OldOperationStatus.todo.raw: status_conf["TODO"],
            OldOperationStatus.blocked.raw: status_conf["BLOCKED"],
        }

        return status_map[status_name]
    except (TypeError, KeyError):
        return status_name


def load_old_operation_status(foo, bar):
    for st_id, st_name in OldOperationStatus():
        OperationStatus.objects.create(id=st_id, name=safe_convert_status(st_name))


class Migration(migrations.Migration):
    dependencies = [
        ("operations", "0009_auto_20170403_1112"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationStatus",
            fields=[
                (
                    "id",
                    models.AutoField(
                        serialize=False,
                        primary_key=True,
                        auto_created=True,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(verbose_name="name", max_length=255, unique=True),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.RunPython(load_old_operation_status, atomic=True),
        migrations.AlterField(
            model_name="operation",
            name="status",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="operations.OperationStatus",
                verbose_name="status",
            ),
        ),
    ]
