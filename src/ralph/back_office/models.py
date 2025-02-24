# -*- coding: utf-8 -*-
import datetime
import logging
import re
from functools import partial

from dj.choices import Choices, Country
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import models, transaction
from django.forms import ValidationError
from django.template import Context, Template
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Regionalizable
from ralph.assets.country_utils import iso2_to_iso3
from ralph.assets.models.assets import (
    Asset,
    AssetLastHostname,
    AssetModel,
    ServiceEnvironment
)
from ralph.assets.utils import move_parents_models
from ralph.attachments.utils import send_transition_attachments_to_user
from ralph.lib.hooks import get_hook
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import (
    AdminAbsoluteUrlMixin,
    NamedMixin,
    TimeStampMixin
)
from ralph.lib.transitions.conf import get_report_name_for_transition_id
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.fields import TransitionField
from ralph.lib.transitions.models import Transition
from ralph.licences.models import BaseObjectLicence, Licence
from ralph.reports.helpers import generate_report
from ralph.reports.models import ReportLanguage

IMEI_UNTIL_2003 = re.compile(r"^\d{6} *\d{2} *\d{6} *\d$")
IMEI_SINCE_2003 = re.compile(r"^\d{8} *\d{6} *\d$")
ASSET_HOSTNAME_TEMPLATE = getattr(settings, "ASSET_HOSTNAME_TEMPLATE", None)
if not ASSET_HOSTNAME_TEMPLATE:
    raise ImproperlyConfigured('"ASSET_HOSTNAME_TEMPLATE" must be specified.')

logger = logging.getLogger(__name__)


class Warehouse(AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model):
    _allow_in_dashboard = True
    stocktaking_enabled = models.BooleanField(default=False)
    stocktaking_tag_suffix = models.CharField(max_length=8, default="", blank=True)


class BackOfficeAssetStatus(Choices):
    _ = Choices.Choice

    new = _("new")
    in_progress = _("in progress")
    waiting_for_release = _("waiting for release")
    used = _("in use")
    loan = _("loan")
    damaged = _("damaged")
    liquidated = _("liquidated")
    in_service = _("in service")
    installed = _("installed")
    free = _("free")
    reserved = _("reserved")
    sale = _("sale")
    loan_in_progress = _("loan in progress")
    return_in_progress = _("return in progress")
    to_find = _("to find")
    sent = _("sent")
    to_buyout = _("to buyout")
    in_use_team = _("in use team")
    in_use_test = _("in use test")
    in_progress_team = _("in progress team")
    in_progress_test = _("in progress test")
    quarantine = _("quarantine")
    refurbished = _("refurbished")
    reserved_to_order = _("reserved to order")
    replacement = _("replacement")


class OfficeInfrastructure(
    AdminAbsoluteUrlMixin, NamedMixin, TimeStampMixin, models.Model
):
    class Meta:
        verbose_name = _("Office Infrastructure")
        verbose_name_plural = _("Office Infrastructures")


def _is_field_in_transition_actions(actions, field_name):
    """
    Returns True if there is field with given name in one of actions.
    """
    for action in actions:
        if field_name in getattr(action, "form_fields", {}):
            return True
    return False


def get_user_iso3_country_name(user):
    """
    :param user: instance of django.contrib.auth.models.User which has profile
        with country attribute
    """
    country_name = Country.name_from_id(int(user.country))
    iso3_country_name = iso2_to_iso3(country_name)
    return iso3_country_name


def _check_assets_owner(instances, **kwargs):
    errors = {}
    requester = kwargs.get("requester", None)
    if not requester:
        return {"__all__": _("requester must be specified")}
    for instance in instances:
        if requester and instance.owner != requester:
            errors[instance] = _("requester is not an owner of the asset")
    return errors


def _check_assets_user(instances, **kwargs):
    errors = {}
    requester = kwargs.get("requester", None)
    if not requester:
        return {"__all__": _("requester must be specified")}
    for instance in instances:
        if requester and instance.user != requester:
            errors[instance] = _("requester is not an user of the asset")
    return errors


def _check_user_assigned(instances, **kwargs):
    errors = {}
    for instance in instances:
        if not instance.user:
            errors[instance] = _("user not assigned")
    return errors


def autocomplete_user(actions, objects, field_name="user"):
    """Returns default value for user transition field.

    When multiple assets are selected, default user/owner is returned only if
    all assets have the same user assigned. Otherwise None will be returned.

    Args:
        actions: Transition action list
        objects: Django models objects
        field_name: String of name for user field

    Returns:
        String value of user pk
    """
    users = [getattr(obj, field_name, None) for obj in objects]

    if len(set(users)) == 1 and users[0]:
        return str(users[0].pk)
    else:
        return None


class BackOfficeAsset(Regionalizable, Asset):
    _allow_in_dashboard = True

    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="assets_as_owner",
        on_delete=models.CASCADE,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="assets_as_user",
        on_delete=models.CASCADE,
    )
    location = models.CharField(max_length=128, null=True, blank=True)
    purchase_order = models.CharField(max_length=50, null=True, blank=True)
    loan_end_date = models.DateField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_("Loan end date"),
    )
    status = TransitionField(
        default=BackOfficeAssetStatus.new.id,
        choices=BackOfficeAssetStatus(),
    )
    imei = NullableCharField(
        max_length=18, null=True, blank=True, unique=True, verbose_name=_("IMEI")
    )
    imei2 = NullableCharField(
        max_length=18, null=True, blank=True, unique=True, verbose_name=_("IMEI 2")
    )
    office_infrastructure = models.ForeignKey(
        OfficeInfrastructure, null=True, blank=True, on_delete=models.CASCADE
    )
    last_status_change = models.DateField(
        null=True, blank=True, default=None, verbose_name=_("Last status change")
    )

    class Meta:
        verbose_name = _("Back Office Asset")
        verbose_name_plural = _("Back Office Assets")

    @property
    def country_code(self):
        iso2 = Country.name_from_id(int(self.region.country)).upper()
        return iso2_to_iso3(iso2)

    def __str__(self):
        return "{} (BC: {} / SN: {})".format(
            self.hostname or "-", self.barcode or "-", self.sn or "-"
        )

    def __repr__(self):
        return "<BackOfficeAsset: {}>".format(self.id)

    def validate_imei(self, imei):
        return IMEI_SINCE_2003.match(imei) or IMEI_UNTIL_2003.match(imei)

    def clean(self):
        super().clean()
        if self.imei and not self.validate_imei(self.imei):
            raise ValidationError(
                {"imei": _("%(imei)s is not IMEI format") % {"imei": self.imei}}
            )
        if self.imei2 and not self.validate_imei(self.imei2):
            raise ValidationError(
                {
                    "imei2": _("%(imei)s is not IMEI format") % {"imei": self.imei2}  # noqa
                }
            )

    def is_liquidated(self, date=None):
        date = date or datetime.date.today()
        # check if asset has status 'liquidated' and if yes, check if it has
        # this status on given date
        if self.status == BackOfficeAssetStatus.liquidated and self._liquidated_at(
            date
        ):
            return True
        return False

    def generate_hostname(self, commit=True, template_vars=None):
        def render_template(template):
            template = Template(template)
            context = Context(template_vars or {})
            return template.render(context)

        logger.info(
            "Generating new hostname for %s using %s old hostname %s",
            self,
            template_vars,
            self.hostname,
        )
        prefix = render_template(
            ASSET_HOSTNAME_TEMPLATE.get("prefix", ""),
        )
        postfix = render_template(
            ASSET_HOSTNAME_TEMPLATE.get("postfix", ""),
        )
        counter_length = ASSET_HOSTNAME_TEMPLATE.get("counter_length", 5)
        last_hostname = AssetLastHostname.increment_hostname(prefix, postfix)
        self.hostname = last_hostname.formatted_hostname(fill=counter_length)
        if commit:
            self.save()

    # TODO: add message when hostname was changed
    def _try_assign_hostname(self, commit=False, country=None, force=False):
        if self.model.category and self.model.category.code:
            template_vars = {
                "code": self.model.category.code,
                "country_code": country or self.country_code,
            }
            if force or not self.hostname or self.country_code not in self.hostname:
                self.generate_hostname(commit, template_vars)

    @classmethod
    def get_autocomplete_queryset(cls):
        return cls._default_manager.exclude(status=BackOfficeAssetStatus.liquidated.id)

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
            "owner": {
                "field": forms.CharField(label=_("Owner")),
                "autocomplete_field": "owner",
                "default_value": partial(autocomplete_user, field_name="owner"),
            }
        },
        help_text=_(
            "During this transition owner will be assigned as well as new "
            "hostname might be generated for asset (only for particular model "
            "categories and only if owner's country has changed)"
        ),
        run_after=["unassign_owner"],
    )
    def assign_owner(cls, instances, **kwargs):
        owner = get_user_model().objects.get(pk=int(kwargs["owner"]))
        for instance in instances:
            instance.owner = owner

    @classmethod
    @transition_action(
        form_fields={
            "licences": {
                "field": forms.ModelMultipleChoiceField(
                    queryset=Licence.objects.all(),
                    label=_("Licence"),
                    required=False,
                ),
                "autocomplete_field": "licence",
                "autocomplete_model": "licences.BaseObjectLicence",
                "widget_options": {"multi": True},
            }
        },
        run_after=["unassign_licences"],
    )
    def assign_licence(cls, instances, **kwargs):
        for instance in instances:
            for obj in kwargs["licences"]:
                BaseObjectLicence.objects.get_or_create(
                    base_object=instance,
                    licence_id=obj.id,
                )

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
            "loan_end_date": {
                "field": forms.DateField(
                    label=_("Loan end date"),
                    widget=forms.TextInput(attrs={"class": "datepicker"}),
                )
            }
        },
    )
    def assign_loan_end_date(cls, instances, **kwargs):
        for instance in instances:
            instance.loan_end_date = kwargs["loan_end_date"]

    @classmethod
    @transition_action()
    def unassign_loan_end_date(cls, instances, **kwargs):
        for instance in instances:
            instance.loan_end_date = None

    @classmethod
    @transition_action(
        form_fields={
            "warehouse": {
                "field": forms.CharField(label=_("Warehouse")),
                "autocomplete_field": "warehouse",
            }
        }
    )
    def assign_warehouse(cls, instances, **kwargs):
        warehouse = Warehouse.objects.get(pk=int(kwargs["warehouse"]))
        for instance in instances:
            instance.warehouse = warehouse

    @classmethod
    @transition_action(
        form_fields={
            "office_infrastructure": {
                "field": forms.CharField(label=_("Office infrastructure")),
                "autocomplete_field": "office_infrastructure",
            }
        },
    )
    def assign_office_infrastructure(cls, instances, **kwargs):
        office_inf = OfficeInfrastructure.objects.get(
            pk=int(kwargs["office_infrastructure"])
        )
        for instance in instances:
            instance.office_infrastructure = office_inf

    @classmethod
    @transition_action(
        form_fields={
            "remarks": {
                "field": forms.CharField(label=_("Remarks")),
            }
        }
    )
    def add_remarks(cls, instances, **kwargs):
        for instance in instances:
            instance.remarks = "{}\n{}".format(instance.remarks, kwargs["remarks"])

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
    def unassign_licences(cls, instances, **kwargs):
        BaseObjectLicence.objects.filter(base_object__in=instances).delete()

    @classmethod
    @transition_action(
        form_fields={
            "country": {
                "field": forms.ChoiceField(
                    label=_("Country"),
                    choices=Country(),
                    **{
                        "initial": Country.from_name(
                            settings.CHANGE_HOSTNAME_ACTION_DEFAULT_COUNTRY.lower()  # noqa: E501
                        ).id
                    }
                    if settings.CHANGE_HOSTNAME_ACTION_DEFAULT_COUNTRY
                    else {},
                ),
            }
        },
    )
    def change_hostname(cls, instances, **kwargs):
        country_id = kwargs["country"]
        country_name = Country.name_from_id(int(country_id)).upper()
        iso3_country_name = iso2_to_iso3(country_name)
        for instance in instances:
            instance._try_assign_hostname(country=iso3_country_name, force=True)

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

    @classmethod
    def _get_report_context(cls, instances):
        data_instances = [
            {
                "sn": obj.sn,
                "model": str(obj.model),
                "imei": obj.imei,
                "imei2": obj.imei2,
                "barcode": obj.barcode,
            }
            for obj in instances
        ]
        return data_instances

    @classmethod
    @transition_action(precondition=_check_assets_owner)
    def must_be_owner_of_asset(cls, instances, **kwargs):
        """Only a precondition matters"""
        pass

    @classmethod
    @transition_action(precondition=_check_assets_user)
    def must_be_user_of_asset(cls, instances, **kwargs):
        """Only a precondition matters"""
        pass

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
    @transition_action(run_after=["release_report"])
    def assign_requester_as_an_owner(cls, instances, requester, **kwargs):
        """Assign current user as an owner"""
        for instance in instances:
            instance.owner = requester
            instance.save()

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
    @transition_action(run_after=["release_report", "return_report", "loan_report"])
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
            "report_language": {
                "field": forms.ModelChoiceField(
                    label=_("Return report language"),
                    queryset=ReportLanguage.objects.all().order_by("-default"),
                    empty_label=None,
                ),
                "exclude_from_history": True,
            },
        },
        return_attachment=True,
        precondition=_check_user_assigned,
    )
    def return_report(cls, instances, requester, **kwargs):
        return generate_report(
            instances=instances,
            name="return",
            requester=requester,
            language=kwargs["report_language"],
            context=cls._get_report_context(instances),
        )

    @classmethod
    @transition_action(
        form_fields={
            "report_language": {
                "field": forms.ModelChoiceField(
                    label=_("Loan report language"),
                    queryset=ReportLanguage.objects.all().order_by("-default"),
                    empty_label=None,
                ),
                "exclude_from_history": True,
            }
        },
        return_attachment=True,
        run_after=["assign_owner", "assign_user", "assign_loan_end_date"],
    )
    def loan_report(cls, instances, requester, **kwargs):
        return generate_report(
            name="loan",
            requester=requester,
            instances=instances,
            language=kwargs["report_language"],
            context=cls._get_report_context(instances),
        )

    @classmethod
    @transition_action(
        verbose_name=_("Convert to DataCenter Asset"),
        disable_save_object=True,
        only_one_action=True,
        form_fields={
            "rack": {
                "field": forms.CharField(label=_("Rack")),
                "autocomplete_field": "rack",
                "autocomplete_model": "data_center.DataCenterAsset",
            },
            "position": {
                "field": forms.IntegerField(label=_("Position")),
            },
            "model": {
                "field": forms.CharField(label=_("Model")),
                "autocomplete_field": "model",
                "autocomplete_model": "data_center.DataCenterAsset",
            },
            "service_env": {
                "field": forms.CharField(label=_("Service env")),
                "autocomplete_field": "service_env",
                "autocomplete_model": "data_center.DataCenterAsset",
            },
        },
    )
    def convert_to_data_center_asset(cls, instances, **kwargs):
        from ralph.data_center.models.physical import DataCenterAsset, Rack  # noqa
        from ralph.back_office.helpers import bo_asset_to_dc_asset_status_converter  # noqa

        with transaction.atomic():
            for i, instance in enumerate(instances):
                data_center_asset = DataCenterAsset()
                data_center_asset.rack = Rack.objects.get(pk=kwargs["rack"])
                data_center_asset.position = kwargs["position"]
                data_center_asset.service_env = ServiceEnvironment.objects.get(
                    pk=kwargs["service_env"]
                )
                data_center_asset.model = AssetModel.objects.get(pk=kwargs["model"])
                target_status = int(
                    Transition.objects.values_list("target", flat=True).get(
                        pk=kwargs["transition_id"]
                    )  # noqa
                )
                data_center_asset.status = bo_asset_to_dc_asset_status_converter(  # noqa
                    instance.status, target_status
                )
                move_parents_models(
                    instance,
                    data_center_asset,
                    exclude_copy_fields=["rack", "model", "service_env", "status"],
                )
                data_center_asset.save()
                # Save new asset to list, required to redirect url.
                # RunTransitionView.get_success_url()
                instances[i] = data_center_asset

    @classmethod
    @transition_action()
    def assign_hostname_if_empty_or_country_not_match(cls, instances, **kwargs):
        if settings.BACK_OFFICE_ASSET_AUTO_ASSIGN_HOSTNAME:
            for instance in instances:
                instance._try_assign_hostname(commit=False, force=False)

    @classmethod
    @transition_action()
    def last_status(cls, instances, **kwargs):
        for instance in instances:
            instance.last_status_change = datetime.date.today()

    @classmethod
    @transition_action()
    def hardware_replacement(cls, instances, **kwargs):
        for instance in instances:
            instance.loan_end_date = datetime.date.today() + datetime.timedelta(days=10)  # noqa
