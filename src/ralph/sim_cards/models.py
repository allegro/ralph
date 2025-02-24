import datetime
from functools import partial

from dj.choices import Choices
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import (
    MaxLengthValidator,
    MinLengthValidator,
    RegexValidator
)
from django.db import models
from django.utils.translation import ugettext_lazy as _

from ralph.assets.models import AssetHolder
from ralph.attachments.utils import send_transition_attachments_to_user
from ralph.back_office.models import autocomplete_user, Warehouse
from ralph.lib.hooks import get_hook
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)
from ralph.lib.transitions.conf import get_report_name_for_transition_id
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import TransitionWorkflowBase
from ralph.reports.helpers import generate_report
from ralph.reports.models import ReportLanguage

PUK_CODE_VALIDATORS = [
    MinLengthValidator(5),
    RegexValidator(regex=r"^\d+$", message=_("Required numeric characters only.")),
]


PIN_CODE_VALIDATORS = [
    MinLengthValidator(4),
    RegexValidator(regex=r"^\d+$", message=_("Required numeric characters only.")),
]


class SIMCardStatus(Choices):
    _ = Choices.Choice

    new = _("new")
    in_progress = _("in progress")
    waiting_for_release = _("waiting for release")
    used = _("in use")
    damaged = _("damaged")
    liquidated = _("liquidated")
    free = _("free")
    reserved = _("reserved")
    loan_in_progress = _("loan in progress")
    return_in_progress = _("return in progress")
    in_quarantine = _("in quarantine")


class CellularCarrier(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    pass


class SIMCardFeatures(AdminAbsoluteUrlMixin, NamedMixin, models.Model):
    pass


class SIMCard(
    AdminAbsoluteUrlMixin,
    TimeStampMixin,
    models.Model,
    metaclass=TransitionWorkflowBase,
):
    pin1 = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        help_text=_("Required numeric characters only."),
        validators=PIN_CODE_VALIDATORS,
    )
    puk1 = models.CharField(
        max_length=16,
        help_text=_("Required numeric characters only."),
        validators=PUK_CODE_VALIDATORS,
    )
    pin2 = models.CharField(
        max_length=8,
        null=True,
        blank=True,
        help_text=_("Required numeric characters only."),
        validators=PIN_CODE_VALIDATORS,
    )
    puk2 = models.CharField(
        max_length=16,
        null=True,
        blank=True,
        help_text=_("Required numeric characters only."),
        validators=PUK_CODE_VALIDATORS,
    )
    carrier = models.ForeignKey(
        CellularCarrier,
        on_delete=models.PROTECT,
    )
    card_number = models.CharField(
        max_length=22,
        unique=True,
        validators=[
            MinLengthValidator(1),
            MaxLengthValidator(22),
            RegexValidator(
                regex=r"^\d+$",
                message=_("Required numeric characters only."),
            ),
        ],
    )
    phone_number = models.CharField(
        max_length=16,
        unique=True,
        help_text=_("ex. +2920181234"),
        validators=[
            MinLengthValidator(1),
            MaxLengthValidator(16),
            RegexValidator(
                regex=r"^\+\d+$", message="Phone number must have +2920181234 format."
            ),
        ],
    )
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="owned_simcards",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="used_simcards",
    )
    status = TransitionField(
        default=SIMCardStatus.new.id,
        choices=SIMCardStatus(),
    )
    remarks = models.TextField(blank=True)
    quarantine_until = models.DateField(
        null=True, blank=True, help_text=_("End of quarantine date.")
    )
    features = models.ManyToManyField(
        SIMCardFeatures,
        blank=True,
    )
    property_of = models.ForeignKey(
        AssetHolder,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    def __str__(self):
        return _("SIM Card: {}").format(self.phone_number)

    @classmethod
    @transition_action(
        form_fields={
            "user": {
                "field": forms.CharField(label=_("User")),
                "autocomplete_field": "user",
                "default_value": partial(autocomplete_user, field_name="user"),
            }
        },
        run_after=["unassign_user"],
    )
    def assign_user(cls, instances, **kwargs):
        user = get_user_model().objects.get(pk=int(kwargs["user"]))
        for instance in instances:
            instance.user = user

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
    def _get_report_context(cls, instances):
        context = [
            {
                "card_number": obj.card_number,
                "carrier": obj.carrier.name,
                "pin1": obj.pin1,
                "puk1": obj.puk1,
                "phone_number": obj.phone_number,
            }
            for obj in instances
        ]
        return context

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
            "owner": {
                "field": forms.CharField(label=_("Owner")),
                "autocomplete_field": "owner",
                "default_value": partial(autocomplete_user, field_name="owner"),
            }
        },
        help_text=_("assign owner"),
        run_after=["unassign_owner"],
    )
    def assign_owner(cls, instances, **kwargs):
        owner = get_user_model().objects.get(pk=int(kwargs["owner"]))
        for instance in instances:
            instance.owner = owner

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
    @transition_action(
        form_fields={
            "warehouse": {
                "field": forms.CharField(label=_("Warehouse")),
                "autocomplete_field": "warehouse",
                "default_value": partial(autocomplete_user, field_name="warehouse"),
            }
        }
    )
    def assign_warehouse(cls, instances, **kwargs):
        warehouse = Warehouse.objects.get(pk=int(kwargs["warehouse"]))
        for instance in instances:
            instance.warehouse = warehouse

    @classmethod
    @transition_action(run_after=["loan_report", "return_report"])
    def unassign_owner(cls, instances, **kwargs):
        for instance in instances:
            kwargs["history_kwargs"][instance.pk]["affected_owner"] = str(
                instance.owner
            )
            instance.owner = None

    @classmethod
    @transition_action(run_after=["loan_report", "return_report"])
    def unassign_user(cls, instances, **kwargs):
        for instance in instances:
            kwargs["history_kwargs"][instance.pk]["affected_user"] = str(instance.user)
            instance.user = None

    @classmethod
    @transition_action(
        form_fields={
            "task_url": {
                "field": forms.URLField(label=_("task URL")),
            }
        }
    )
    def assign_task_url(cls, instances, **kwargs):
        for instance in instances:
            instance.task_url = kwargs["task_url"]

    @classmethod
    @transition_action()
    def quarantine_date(cls, instances, **kwargs):
        for instance in instances:
            instance.quarantine_until = datetime.date.today() + datetime.timedelta(
                days=90
            )  # noqa

    @classmethod
    @transition_action(
        form_fields={
            "pin1": {
                "field": forms.CharField(label=_("pin1")),
            },
            "puk1": {
                "field": forms.CharField(label=_("puk1")),
            },
        }
    )
    def change_pin_and_puk(cls, instances, **kwargs):
        for instance in instances:
            instance.pin1 = kwargs["pin1"]
            instance.puk1 = kwargs["puk1"]

    @classmethod
    @transition_action(
        form_fields={
            "card number": {
                "field": forms.CharField(label=_("card number")),
            }
        }
    )
    def card_number_to_notes(cls, instances, **kwargs):
        for instance in instances:
            instance.remarks = "{}\n{}".format(instance.remarks, instance.card_number)
            instance.card_number = kwargs["card number"]

    @classmethod
    @transition_action(
        form_fields={
            "user": {
                "field": forms.CharField(label=_("User")),
                "autocomplete_field": "user",
            },
            "owner": {
                "field": forms.CharField(label=_("Owner")),
                "autocomplete_field": "owner",
                "condition": lambda obj, actions: bool(obj.owner),
            },
        }
    )
    def change_user_and_owner(cls, instances, **kwargs):
        UserModel = get_user_model()  # noqa
        user_id = kwargs.get("user", None)
        user = UserModel.objects.get(id=user_id)
        owner_id = kwargs.get("owner", None)
        for instance in instances:
            instance.user = user
            if not owner_id:
                instance.owner = user
            else:
                instance.owner = UserModel.objects.get(id=owner_id)
            instance.location = user.location
