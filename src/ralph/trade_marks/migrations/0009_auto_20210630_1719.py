# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import django
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("trade_marks", "0008_auto_20210625_0738"),
    ]

    operations = [
        migrations.RenameField(
            model_name="design",
            old_name="registrant_class",
            new_name="classes",
        ),
        migrations.RenameField(
            model_name="design",
            old_name="registrant_number",
            new_name="number",
        ),
        migrations.RenameField(
            model_name="patent",
            old_name="registrant_class",
            new_name="classes",
        ),
        migrations.RenameField(
            model_name="patent",
            old_name="registrant_number",
            new_name="number",
        ),
        migrations.RenameField(
            model_name="trademark",
            old_name="registrant_class",
            new_name="classes",
        ),
        migrations.RenameField(
            model_name="trademark",
            old_name="registrant_number",
            new_name="number",
        ),
        migrations.AlterField(
            model_name="design",
            name="holder",
            field=models.ForeignKey(
                blank=True,
                null=True,
                to="assets.AssetHolder",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="design",
            name="status",
            field=models.PositiveIntegerField(
                default=5,
                choices=[
                    (1, "Application filed"),
                    (2, "Application refused"),
                    (3, "Application withdrawn"),
                    (4, "Application opposed"),
                    (5, "Registered"),
                    (6, "Registration invalidated"),
                    (7, "Registration expired"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="design",
            name="type",
            field=models.PositiveIntegerField(
                default=2,
                choices=[(1, "Word"), (2, "Figurative"), (3, "Word - Figurative")],
            ),
        ),
        migrations.AlterField(
            model_name="patent",
            name="holder",
            field=models.ForeignKey(
                blank=True,
                null=True,
                to="assets.AssetHolder",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="patent",
            name="status",
            field=models.PositiveIntegerField(
                default=5,
                choices=[
                    (1, "Application filed"),
                    (2, "Application refused"),
                    (3, "Application withdrawn"),
                    (4, "Application opposed"),
                    (5, "Registered"),
                    (6, "Registration invalidated"),
                    (7, "Registration expired"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="patent",
            name="type",
            field=models.PositiveIntegerField(
                default=2,
                choices=[(1, "Word"), (2, "Figurative"), (3, "Word - Figurative")],
            ),
        ),
        migrations.AlterField(
            model_name="trademark",
            name="holder",
            field=models.ForeignKey(
                blank=True,
                null=True,
                to="assets.AssetHolder",
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AlterField(
            model_name="trademark",
            name="status",
            field=models.PositiveIntegerField(
                default=5,
                choices=[
                    (1, "Application filed"),
                    (2, "Application refused"),
                    (3, "Application withdrawn"),
                    (4, "Application opposed"),
                    (5, "Registered"),
                    (6, "Registration invalidated"),
                    (7, "Registration expired"),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="trademark",
            name="type",
            field=models.PositiveIntegerField(
                default=2,
                choices=[(1, "Word"), (2, "Figurative"), (3, "Word - Figurative")],
            ),
        ),
    ]
