# -*- coding: utf-8 -*-
import datetime
import logging
import os
import re
import tempfile
from functools import partial

from dj.choices import Choices, Country
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Regionalizable
from ralph.assets.country_utils import iso2_to_iso3
from ralph.assets.models.assets import Asset, AssetModel, ServiceEnvironment
from ralph.assets.utils import move_parents_models
from ralph.attachments.helpers import add_attachment_from_disk
from ralph.lib.external_services import ExternalService, obj_to_dict
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import NamedMixin, TimeStampMixin
from ralph.lib.transitions import transition_action, TransitionField
from ralph.licences.models import BaseObjectLicence, Licence
from ralph.reports.models import Report, ReportLanguage

IMEI_UNTIL_2003 = re.compile(r'^\d{6} *\d{2} *\d{6} *\d$')
IMEI_SINCE_2003 = re.compile(r'^\d{8} *\d{6} *\d$')

logger = logging.getLogger(__name__)


class Warehouse(NamedMixin, TimeStampMixin, models.Model):
    pass


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


class OfficeInfrastructure(NamedMixin, TimeStampMixin, models.Model):

    class Meta:
        verbose_name = _('Office Infrastructure')
        verbose_name_plural = _('Office Infrastructures')


def _is_field_in_transition_actions(actions, field_name):
    """
    Returns True if there is field with given name in one of actions.
    """
    for action in actions:
        if field_name in getattr(action, 'form_fields', {}):
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


def _check_user_assigned(instances):
    errors = {}
    for instance in instances:
        if not instance.user:
            errors[instance] = _('user not assigned')
    return errors


def autocomplete_if_release_report(actions, objects, field_name='user'):
    """
    Returns value of the first item in the list objects of the field_name
    if release_report is actions.

    Args:
        actions: Transition action list
        objects: Django models objects
        field_name: String of name

    Returns:
        String value from object
    """
    try:
        obj = objects[0]
    except IndexError:
        return None

    value = getattr(obj, field_name, None)
    if value:
        for action in actions:
            if action.__name__ == 'release_report':
                return str(value.pk)
    return None


class BackOfficeAsset(Regionalizable, Asset):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='assets_as_owner',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        related_name='assets_as_user',
    )
    location = models.CharField(max_length=128, null=True, blank=True)
    purchase_order = models.CharField(max_length=50, null=True, blank=True)
    loan_end_date = models.DateField(
        null=True, blank=True, default=None, verbose_name=_('Loan end date'),
    )
    status = TransitionField(
        default=BackOfficeAssetStatus.new.id,
        choices=BackOfficeAssetStatus(),
    )
    imei = NullableCharField(
        max_length=18, null=True, blank=True, unique=True
    )
    office_infrastructure = models.ForeignKey(
        OfficeInfrastructure, null=True, blank=True
    )

    class Meta:
        verbose_name = _('Back Office Asset')
        verbose_name_plural = _('Back Office Assets')

    @property
    def country_code(self):
        iso2 = Country.name_from_id(int(self.region.country)).upper()
        return iso2_to_iso3(iso2)

    def __str__(self):
        return '{}'.format(self.hostname or self.barcode or self.sn)

    def __repr__(self):
        return '<BackOfficeAsset: {}>'.format(self.id)

    def validate_imei(self):
        return IMEI_SINCE_2003.match(self.imei) or \
            IMEI_UNTIL_2003.match(self.imei)

    def clean(self):
        super().clean()
        if self.imei and not self.validate_imei():
            raise ValidationError({
                'imei': _('%(imei)s is not IMEI format') % {'imei': self.imei}
            })

    def is_liquidated(self, date=None):
        date = date or datetime.date.today()
        # check if asset has status 'liquidated' and if yes, check if it has
        # this status on given date
        if (
            self.status == BackOfficeAssetStatus.liquidated and
            self._liquidated_at(date)
        ):
            return True
        return False

    def _try_assign_hostname(
        self, commit=False, country=None, force=False, request=None
    ):
        if self.model.category and self.model.category.code:
            template_vars = {
                'code': self.model.category.code,
                'country_code': country or self.country_code,
            }
            if (
                force or
                not self.hostname or
                self.country_code not in self.hostname
            ):
                self.generate_hostname(commit, template_vars, request)

    @classmethod
    def get_autocomplete_queryset(cls):
        return cls._default_manager.exclude(
            status=BackOfficeAssetStatus.liquidated.id
        )

    @classmethod
    @transition_action(
        form_fields={
            'user': {
                'field': forms.CharField(label=_('User')),
                'autocomplete_field': 'user',
                'default_value': partial(
                    autocomplete_if_release_report, field_name='user'
                )
            }
        },
    )
    def assign_user(cls, instances, request, **kwargs):
        user = get_user_model().objects.get(pk=int(kwargs['user']))
        for instance in instances:
            instance.user = user

    @classmethod
    @transition_action(
        form_fields={
            'licences': {
                'field': forms.ModelMultipleChoiceField(
                    queryset=Licence.objects.all(), label=_('Licence')
                ),
                'autocomplete_field': 'licence',
                'autocomplete_model': 'licences.BaseObjectLicence',
                'widget_options': {'multi': True},
            }
        }
    )
    def assign_licence(cls, instances, request, **kwargs):
        for instance in instances:
            for obj in kwargs['licences']:
                BaseObjectLicence.objects.get_or_create(
                    base_object=instance, licence_id=obj.id,
                )

    @classmethod
    @transition_action(
        form_fields={
            'owner': {
                'field': forms.CharField(label=_('Owner')),
                'autocomplete_field': 'owner',
                'default_value': partial(
                    autocomplete_if_release_report, field_name='owner'
                )
            }
        },
        help_text=_(
            'During this transition owner will be assigned as well as new '
            'hostname might be generated for asset (only for particular model '
            'categories and only if owner\'s country has changed)'
        ),
    )
    def assign_owner(cls, instances, request, **kwargs):
        owner = get_user_model().objects.get(pk=int(kwargs['owner']))
        for instance in instances:
            instance.owner = owner

    @classmethod
    @transition_action(
        run_after=['loan_report', 'return_report']
    )
    def unassign_owner(cls, instances, request, **kwargs):
        for instance in instances:
            kwargs['history_kwargs'][instance.pk][
                'affected_owner'
            ] = str(instance.owner)
            instance.owner = None

    @classmethod
    @transition_action(
        run_after=['loan_report', 'return_report']
    )
    def unassign_user(cls, instances, request, **kwargs):
        for instance in instances:
            kwargs['history_kwargs'][instance.pk][
                'affected_user'
            ] = str(instance.user)
            instance.user = None

    @classmethod
    @transition_action(
        form_fields={
            'loan_end_date': {
                'field': forms.DateField(
                    label=_('Loan end date'),
                    widget=forms.TextInput(attrs={'class': 'datepicker'})
                )
            }
        },
    )
    def assign_loan_end_date(cls, instances, request, **kwargs):
        for instance in instances:
            instance.loan_end_date = kwargs['loan_end_date']

    @classmethod
    @transition_action()
    def unassign_loan_end_date(cls, instances, request, **kwargs):
        for instance in instances:
            instance.loan_end_date = None

    @classmethod
    @transition_action(
        form_fields={
            'warehouse': {
                'field': forms.CharField(label=_('Warehouse')),
                'autocomplete_field': 'warehouse'
            }
        }
    )
    def assign_warehouse(cls, instances, request, **kwargs):
        warehouse = Warehouse.objects.get(pk=int(kwargs['warehouse']))
        for instance in instances:
            instance.warehouse = warehouse

    @classmethod
    @transition_action(
        form_fields={
            'office_infrastructure': {
                'field': forms.CharField(label=_('Office infrastructure')),
                'autocomplete_field': 'office_infrastructure'
            }
        },
    )
    def assign_office_infrastructure(cls, instances, request, **kwargs):
        office_inf = OfficeInfrastructure.objects.get(
            pk=int(kwargs['office_infrastructure'])
        )
        for instance in instances:
            instance.office_infrastructure = office_inf

    @classmethod
    @transition_action(
        form_fields={
            'remarks': {
                'field': forms.CharField(label=_('Remarks')),
            }
        }
    )
    def add_remarks(cls, instances, request, **kwargs):
        for instance in instances:
            instance.remarks = '{}\n{}'.format(
                instance.remarks, kwargs['remarks']
            )

    @classmethod
    @transition_action(
        form_fields={
            'task_url': {
                'field': forms.URLField(label=_('task URL')),
            }
        }
    )
    def assign_task_url(cls, instances, request, **kwargs):
        for instance in instances:
            instance.task_url = kwargs['task_url']

    @classmethod
    @transition_action()
    def unassign_licences(cls, instances, request, **kwargs):
        BaseObjectLicence.objects.filter(base_object__in=instances).delete()

    @classmethod
    @transition_action(
        form_fields={
            'country': {
                'field': forms.ChoiceField(
                    label=_('Country'),
                    choices=Country(),
                ),
            }
        },
    )
    def change_hostname(cls, instances, request, **kwargs):
        country_id = kwargs['country']
        country_name = Country.name_from_id(int(country_id)).upper()
        iso3_country_name = iso2_to_iso3(country_name)
        for instance in instances:
            instance._try_assign_hostname(
                country=iso3_country_name, force=True, request=request
            )

    @classmethod
    @transition_action(
        form_fields={
            'user': {
                'field': forms.CharField(label=_('User')),
                'autocomplete_field': 'user',
            },
            'owner': {
                'field': forms.CharField(label=_('Owner')),
                'autocomplete_field': 'owner',
                'condition': lambda obj, actions: bool(obj.owner),
            }
        }
    )
    def change_user_and_owner(cls, instances, request, **kwargs):
        UserModel = get_user_model()  # noqa
        user_id = kwargs.get('user', None)
        user = UserModel.objects.get(id=user_id)
        owner_id = kwargs.get('owner', None)
        for instance in instances:
            instance.user = user
            if not owner_id:
                instance.owner = user
            else:
                instance.owner = UserModel.objects.get(id=owner_id)
            instance.location = user.location

    @classmethod
    def _generate_report(cls, name, request, instances, language):
        report = Report.objects.get(name=name)
        template = report.templates.filter(language=language).first()
        if not template:
            template = report.templates.filter(default=True).first()

        template_content = ''
        with open(template.template.path, 'rb') as f:
            template_content = f.read()

        data_instances = [
            {
                'sn': obj.sn,
                'model': str(obj.model),
                'imei': obj.imei,
                'barcode': obj.barcode,
            }
            for obj in instances
        ]
        service_pdf = ExternalService('PDF')
        result = service_pdf.run(
            template=template_content,
            data={
                'id': ', '.join([str(obj.id) for obj in instances]),
                'now': datetime.datetime.now(),
                'logged_user': obj_to_dict(request.user),
                'affected_user': obj_to_dict(instances[0].user),
                'assets': data_instances,
            }
        )
        filename = "_".join([
            timezone.now().isoformat()[:10],
            instances[0].user.get_full_name().lower().replace(' ', '-'),
            name,
        ]) + '.pdf'
        with tempfile.TemporaryDirectory() as tmp_dirpath:
            output_path = os.path.join(tmp_dirpath, filename)
            with open(output_path, 'wb') as f:
                f.write(result)
            return add_attachment_from_disk(
                instances, output_path, request.user,
                _('Document autogenerated by {} transition.').format(name)
            )

    @classmethod
    @transition_action(
        form_fields={
            'report_language': {
                'field': forms.ModelChoiceField(
                    label=_('Report language'),
                    queryset=ReportLanguage.objects.all().order_by('-default'),
                    empty_label=None
                ),
                'exclude_from_history': True
            }
        },
        return_attachment=True,
        run_after=['assign_owner', 'assign_user']
    )
    def release_report(cls, instances, request, **kwargs):
        return cls._generate_report(
            instances=instances, name='release', request=request,
            language=kwargs['report_language']
        )

    @classmethod
    @transition_action(
        form_fields={
            'report_language': {
                'field': forms.ModelChoiceField(
                    label=_('Report language'),
                    queryset=ReportLanguage.objects.all().order_by('-default'),
                    empty_label=None
                ),
                'exclude_from_history': True
            }
        },
        return_attachment=True,
        precondition=_check_user_assigned,
    )
    def return_report(cls, instances, request, **kwargs):
        return cls._generate_report(
            instances=instances, name='return', request=request,
            language=kwargs['report_language']
        )

    @classmethod
    @transition_action(
        form_fields={
            'report_language': {
                'field': forms.ModelChoiceField(
                    label=_('Report language'),
                    queryset=ReportLanguage.objects.all().order_by('-default'),
                    empty_label=None
                ),
                'exclude_from_history': True
            }
        },
        return_attachment=True,
        run_after=['assign_owner', 'assign_user', 'assign_loan_end_date']
    )
    def loan_report(cls, instances, request, **kwargs):
        return cls._generate_report(
            name='loan', request=request, instances=instances,
            language=kwargs['report_language']
        )

    @classmethod
    @transition_action(
        verbose_name=_('Convert to DataCenter Asset'),
        disable_save_object=True,
        only_one_action=True,
        form_fields={
            'rack': {
                'field': forms.CharField(label=_('Rack')),
                'autocomplete_field': 'rack',
                'autocomplete_model': 'data_center.DataCenterAsset'
            },
            'position': {
                'field': forms.IntegerField(label=_('Position')),
            },
            'model': {
                'field': forms.CharField(label=_('Model')),
                'autocomplete_field': 'model',
                'autocomplete_model': 'data_center.DataCenterAsset'
            },
            'service_env': {
                'field': forms.CharField(label=_('Service env')),
                'autocomplete_field': 'service_env',
                'autocomplete_model': 'data_center.DataCenterAsset'
            }
        }
    )
    def convert_to_data_center_asset(cls, instances, request, **kwargs):
        from ralph.data_center.models.physical import DataCenterAsset, Rack  # noqa
        with transaction.atomic():
            for i, instance in enumerate(instances):
                data_center_asset = DataCenterAsset()
                data_center_asset.rack = Rack.objects.get(pk=kwargs['rack'])
                data_center_asset.position = kwargs['position']
                data_center_asset.service_env = ServiceEnvironment.objects.get(
                    pk=kwargs['service_env']
                )
                data_center_asset.model = AssetModel.objects.get(
                    pk=kwargs['model']
                )
                move_parents_models(
                    instance, data_center_asset,
                    exclude_copy_fields=[
                        'rack', 'model', 'service_env'
                    ]
                )
                data_center_asset.save()
                # Save new asset to list, required to redirect url.
                # RunTransitionView.get_success_url()
                instances[i] = data_center_asset


@receiver(pre_save, sender=BackOfficeAsset)
def hostname_assigning(sender, instance, raw, using, **kwargs):
    """Hostname is assigned for new assets with in_progress status or
    edited assets when status has changed to in_progress.
    """
    if getattr(settings, 'BACK_OFFICE_ASSET_AUTO_ASSIGN_HOSTNAME', None):
        if instance.status == BackOfficeAssetStatus.in_progress:
            if instance.pk:
                try:
                    bo_asset = BackOfficeAsset.objects.get(pk=instance.pk)
                except BackOfficeAsset.DoesNotExist:
                    # Can not assign a new hostname, because there are
                    # not yet saved the object.
                    logger.info(
                        'Back office asset does not exists for pk: {}'.format(
                            instance.pk
                        )
                    )
                    return
                if bo_asset.status == BackOfficeAssetStatus.in_progress:
                    return
            logger.info((
                'Status of {} changed to in_progress. Trying to assign new '
                'hostname'
            ).format(instance))
            instance._try_assign_hostname(commit=False)
