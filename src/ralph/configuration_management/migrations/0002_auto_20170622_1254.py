# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ralph.lib.dj_choices import Choices
from ralph.lib.dj_choices.fields import ChoiceField
from django.db import migrations


class SCMCheckResult(Choices):
    _ = Choices.Choice

    scm_ok = _("OK").extra(alert="success", icon_class="fa-check-circle")
    check_failed = _("Check failed").extra(
        alert="warning", icon_class="fa-question-circle"
    )
    scm_error = _("Error").extra(alert="alert", icon_class="fa-exclamation-triangle")


class Migration(migrations.Migration):
    dependencies = [
        ("configuration_management", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="scmstatuscheck",
            name="check_result",
            field=ChoiceField(
                verbose_name="SCM check result",
                choices=SCMCheckResult,
            ),
        ),
    ]
