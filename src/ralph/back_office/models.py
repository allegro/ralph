# -*- coding: utf-8 -*-
import datetime
import os
import re
import tempfile

from dj.choices import Choices, Country
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Regionalizable
from ralph.assets.country_utils import iso2_to_iso3
from ralph.assets.models.assets import Asset
from ralph.attachments.helpers import add_attachment_from_disk
from ralph.lib.external_services import ExternalService, obj_to_dict
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import NamedMixin, TimeStampMixin
from ralph.lib.transitions import transition_action, TransitionField
from ralph.licences.models import BaseObjectLicence
from ralph.reports.models import Report

IMEI_UNTIL_2003 = re.compile(r'^\d{6} *\d{2} *\d{6} *\d$')
IMEI_SINCE_2003 = re.compile(r'^\d{8} *\d{6} *\d$')


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
        if self.owner:
            iso2 = Country.name_from_id(int(self.owner.country)).upper()
            return iso2_to_iso3(iso2)
        return settings.DEFAULT_COUNTRY_CODE

    def __str__(self):
        return '{}'.format(self.hostname or self.barcode or self.sn)

    def __repr__(self):
        return '<BackOfficeAsset: {}>'.format(self.id)

    def validate_imei(self):
        return IMEI_SINCE_2003.match(self.imei) or \
            IMEI_UNTIL_2003.match(self.imei)

    def clean(self):
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

    @classmethod
    @transition_action(
        verbose_name=_('Assign user'),
        form_fields={
            'user': {
                'field': forms.CharField(label=_('User')),
                'autocomplete_field': 'user'
            }
        }
    )
    def assign_user(cls, instances, request, **kwargs):
        user = get_user_model().objects.get(pk=int(kwargs['user']))
        for instance in instances:
            instance.user = user

    @classmethod
    @transition_action(
        verbose_name=_('Assign owner'),
        form_fields={
            'owner': {
                'field': forms.CharField(label=_('Owner')),
                'autocomplete_field': 'owner'
            }
        }
    )
    def assign_owner(cls, instances, request, **kwargs):
        owner = get_user_model().objects.get(pk=int(kwargs['owner']))
        for instance in instances:
            instance.owner = owner

    @classmethod
    @transition_action(
        verbose_name=_('Unassign owner')
    )
    def unassign_owner(cls, instances, request, **kwargs):
        for instance in instances:
            instance.owner = None

    @classmethod
    @transition_action(
        verbose_name=_('Assign user')
    )
    def unassign_user(cls, instances, request, **kwargs):
        for instance in instances:
            instance.user = None

    @classmethod
    @transition_action(
        verbose_name=_('Assign loan end date'),
        form_fields={
            'loan_end_date': {
                'field': forms.CharField(
                    label=_('Loan end date'),
                    widget=forms.TextInput(attrs={'class': 'datepicker'})
                )
            }
        }
    )
    def assign_loan_end_date(cls, instances, request, **kwargs):
        for instance in instances:
            instance.loan_end_date = kwargs['loan_end_date']

    @classmethod
    @transition_action(
        verbose_name=_('Unassign loan end date')
    )
    def unassign_loan_end_date(cls, instances, request, **kwargs):
        for instance in instances:
            instance.loan_end_date = None

    @classmethod
    @transition_action(
        verbose_name=_('Assign warehouse'),
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
        verbose_name=_('Assign office infrastructure')
    )
    def assign_office_infrastructure(cls, instances, request, **kwargs):
        office_inf = OfficeInfrastructure.objects.get(
            pk=int(kwargs['office_infrastructure'])
        )
        for instance in instances:
            instance.office_infrastructure = office_inf

    @classmethod
    @transition_action(
        verbose_name=_('Add remarks'),
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
        verbose_name=_('Assign task URL '),
        form_fields={
            'task_url': {
                'field': forms.CharField(label=_('task_url')),
            }
        }
    )
    def assign_task_url(cls, instances, request, **kwargs):
        for instance in instances:
            instance.task_url = kwargs['task_url']

    @classmethod
    @transition_action(
        verbose_name=_('Unassign licences')
    )
    def unassign_licences(cls, instances, request, **kwargs):
        BaseObjectLicence.objects.filter(base_object__in=instances).delete()

    @classmethod
    @transition_action(
        verbose_name=_('Change hostname'),
        form_fields={
            'country': {
                'field': forms.ChoiceField(
                    label=_('Country'),
                    choices=Country(),
                )
            }
        }
    )
    def change_hostname(cls, instances, request, **kwargs):
        country_id = kwargs['country']
        country_name = Country.name_from_id(int(country_id)).upper()
        iso3_country_name = iso2_to_iso3(country_name)
        for instance in instances:
            template_vars = {
                'code': instance.model.category.code,
                'country_code': iso3_country_name,
            }
            instance.generate_hostname(template_vars=template_vars)

    @classmethod
    @transition_action(
        verbose_name=_('Change user and owner'),
        form_fields={
            'user': {
                'field': forms.CharField(label=_('User')),
                'autocomplete_field': 'user',
            },
            'owner': {
                'field': forms.CharField(label=_('Owner')),
                'autocomplete_field': 'owner',
                'condition': lambda obj: bool(obj.owner),
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
    def _generate_report(cls, name, request, instances):
        report = Report.objects.get(name=name)
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
        output_path = os.path.join(
            tempfile.gettempdir(), '{}-{}.pdf'.format(
                instances[0].user.get_full_name().lower().replace(' ', '-'),
                instances[0].pk
            )
        )
        with open(output_path, 'wb') as f:
            f.write(result)
        return add_attachment_from_disk(
            instances, output_path, request.user,
            _('Document autogenerated by {} transition.').format(name)
        )

    @classmethod
    @transition_action(
        verbose_name=_('Release report'),
        return_attachment=True
    )
    def release_report(cls, instances, request, **kwargs):
        return cls._generate_report(
            instances=instances, name='release', request=request
        )

    @classmethod
    @transition_action(
        verbose_name=_('Return report'),
        return_attachment=True
    )
    def return_report(cls, instances, request, **kwargs):
        return cls._generate_report(
            instances=instances, name='return', request=request
        )

    @classmethod
    @transition_action(
        verbose_name=_('Loan report'),
        return_attachment=True
    )
    def loan_report(cls, instances, request, **kwargs):
        return cls._generate_report(name='loan', request=request)


@receiver(pre_save, sender=BackOfficeAsset)
def hostname_assigning(sender, instance, raw, using, **kwargs):
    """Hostname is assigned for new assets with in_progress status or
    edited assets when status has changed to in_progress.
    """
    if getattr(settings, 'BACK_OFFICE_ASSET_AUTO_ASSIGN_HOSTNAME', None):
        if instance.status == BackOfficeAssetStatus.in_progress:
            if instance.pk:
                bo_asset = BackOfficeAsset.objects.get(pk=instance.pk)
                if bo_asset.status == BackOfficeAssetStatus.in_progress:
                    return
            instance._try_assign_hostname(commit=False)
