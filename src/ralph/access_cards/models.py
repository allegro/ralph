from functools import partial

from dj.choices import Choices
from django import forms
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from mptt.fields import TreeForeignKey, TreeManyToManyField
from mptt.models import MPTTModel

from ralph.accounts.models import RalphUser, Regionalizable
from ralph.attachments.utils import send_transition_attachments_to_user
from ralph.back_office.models import autocomplete_user
from ralph.lib.hooks import get_hook
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin
from ralph.lib.transitions.conf import get_report_name_for_transition_id
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import TransitionWorkflowBaseWithPermissions
from ralph.reports.helpers import generate_report
from ralph.reports.models import ReportLanguage


class AccessCardStatus(Choices):
    _ = Choices.Choice

    new = _("new")
    in_progress = _("in progress")
    lost = _("lost")
    damaged = _("damaged")
    used = _("in use")
    free = _("free")
    return_in_progress = _("return in progress")
    liquidated = _("liquidated")
    reserved = _("reserved")


class AccessZone(AdminAbsoluteUrlMixin, MPTTModel, models.Model):
    name = models.CharField(_("name"), max_length=255)

    class Meta:
        ordering = ["name"]
        unique_together = ["name", "parent"]

    def __str__(self):
        return self.name

    description = models.TextField(
        null=True, blank=True, help_text=_("Optional description")
    )
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        db_index=True,
        on_delete=models.CASCADE,
    )


class AccessCard(
    AdminAbsoluteUrlMixin,
    TimeStampMixin,
    Regionalizable,
    models.Model,
    metaclass=TransitionWorkflowBaseWithPermissions,
):
    visual_number = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_("Number visible on the access card"),
    )
    system_number = models.CharField(
        max_length=255,
        null=False,
        blank=False,
        unique=True,
        help_text=_("Internal number in the access system"),
    )
    issue_date = models.DateField(
        null=True, blank=True, help_text=_("Date of issue to the User")
    )
    notes = models.TextField(null=True, blank=True, help_text=_("Optional notes"))
    user = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name="+",
        help_text=_("User of the card"),
        on_delete=models.SET_NULL,
    )
    owner = models.ForeignKey(
        RalphUser,
        null=True,
        blank=True,
        related_name="+",
        help_text=("Owner of the card"),
        on_delete=models.SET_NULL,
    )
    status = TransitionField(
        choices=AccessCardStatus(),
        default=AccessCardStatus.new.id,
        null=False,
        blank=False,
        help_text=_("Access card status"),
    )
    access_zones = TreeManyToManyField(
        AccessZone, blank=True, related_name="access_cards"
    )

    def __str__(self):
        return _("Access Card: {}").format(self.visual_number)

    @classmethod
    def get_autocomplete_queryset(cls):
        return cls._default_manager.exclude(status=AccessCardStatus.liquidated.id)

    @classmethod
    @transition_action()
    def unassign_user(cls, instances, **kwargs):
        for instance in instances:
            kwargs["history_kwargs"][instance.pk]["affected_user"] = str(instance.user)
            instance.user = None

    @classmethod
    @transition_action(
        form_fields={
            "user": {
                "field": forms.CharField(label=_("User")),
                "autocomplete_field": "user",
                "default_value": partial(autocomplete_user, field_name="user"),
            }
        },
    )
    def assign_user(cls, instances, **kwargs):
        user = get_user_model().objects.get(pk=int(kwargs["user"]))
        for instance in instances:
            instance.user = user

    @classmethod
    @transition_action(
        form_fields={
            "owner": {
                "field": forms.CharField(label=_("Owner")),
                "autocomplete_field": "owner",
                "default_value": partial(autocomplete_user, field_name="owner"),
            }
        },
        help_text=_("assign owner"),
    )
    def assign_owner(cls, instances, **kwargs):
        owner = get_user_model().objects.get(pk=int(kwargs["owner"]))
        for instance in instances:
            instance.owner = owner

    @classmethod
    @transition_action()
    def unassign_owner(cls, instances, **kwargs):
        for instance in instances:
            kwargs["history_kwargs"][instance.pk]["affected_owner"] = str(
                instance.owner
            )
            instance.owner = None

    @classmethod
    @transition_action()
    def clear_access_zones(cls, instances, requester, **kwargs):
        for instance in instances:
            instance.access_zones.clear()

    @classmethod
    @transition_action(
        form_fields={
            "notes": {
                "field": forms.CharField(label=_("notes")),
            }
        }
    )
    def add_notes(cls, instances, **kwargs):
        for instance in instances:
            instance.notes = "{}\n{}".format(instance.notes, kwargs["notes"])

    @classmethod
    @transition_action(run_after=["release_report"])
    def assign_requester_as_an_owner(cls, instances, requester, **kwargs):
        """Assign current user as an owner"""
        for instance in instances:
            instance.owner = requester
            instance.save()

    @classmethod
    @transition_action(
        form_fields={
            "accept": {
                "field": forms.BooleanField(
                    label=_(
                        "I have read and fully understand and " "accept the agreement."
                    )
                )
            },
        }
    )
    def accept_asset_release_agreement(cls, instances, requester, **kwargs):
        pass

    @classmethod
    @transition_action(
        form_fields={
            "report_language": {
                "field": forms.ModelChoiceField(
                    label=_("Release report language"),
                    queryset=ReportLanguage.objects.all().order_by("-default"),
                    empty_label=None,
                ),
                "exclude_from_history": True,
            }
        },
        return_attachment=True,
        run_after=["assign_owner", "assign_user"],
    )
    def release_report(cls, instances, requester, transition_id, **kwargs):
        report_name = get_report_name_for_transition_id(transition_id)
        return generate_report(
            instances=instances,
            name=report_name,
            requester=requester,
            language=kwargs["report_language"],
            context=cls._get_report_context(instances),
        )

    @classmethod
    @transition_action(run_after=["release_report"])
    def send_attachments_to_user(cls, requester, transition_id, **kwargs):
        context_func = get_hook("back_office.transition_action.email_context")
        send_transition_attachments_to_user(
            requester=requester,
            transition_id=transition_id,
            context_func=context_func,
            **kwargs,
        )

    @classmethod
    def _get_report_context(cls, instances):
        context = [
            {
                "visual_number": obj.visual_number,
            }
            for obj in instances
        ]
        return context
