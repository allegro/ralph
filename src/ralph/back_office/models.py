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

    @transition_action
    def assign_user(self, **kwargs):
        self.user = get_user_model().objects.get(pk=int(kwargs['user']))

    assign_user.form_fields = {
        'user': {
            'field': forms.CharField(label=_('User')),
            'autocomplete_field': 'user'
        }
    }
    assign_user.verbose_name = _('Assign user')

    @transition_action
    def assign_owner(self, **kwargs):
        self.owner = get_user_model().objects.get(pk=int(kwargs['owner']))

    assign_owner.form_fields = {
        'owner': {
            'field': forms.CharField(label=_('Owner')),
            'autocomplete_field': 'owner'
        }
    }
    assign_owner.verbose_name = _('Assign owner')

    @transition_action
    def unassign_owner(self, **kwargs):
        self.owner = None
    unassign_owner.verbose_name = _('Unassign owner')

    @transition_action
    def unassign_user(self, **kwargs):
        self.user = None
    unassign_user.verbose_name = _('Unassign user')

    @transition_action
    def assign_loan_end_date(self, **kwargs):
        self.loan_end_date = kwargs['loan_end_date']

    assign_loan_end_date.form_fields = {
        'loan_end_date': {
            'field': forms.CharField(
                label=_('Loan end date'),
                widget=forms.TextInput(attrs={'class': 'datepicker'})
            )
        }
    }
    assign_loan_end_date.verbose_name = _('Assign loan end date')

    @transition_action
    def unassign_loan_end_date(self, **kwargs):
        self.loan_end_date = None
    unassign_loan_end_date.verbose_name = _('Unassign loan end date')

    @transition_action
    def assign_warehouse(self, **kwargs):
        self.warehouse = Warehouse.objects.get(pk=int(kwargs['warehouse']))

    assign_warehouse.form_fields = {
        'warehouse': {
            'field': forms.CharField(label=_('Warehouse')),
            'autocomplete_field': 'warehouse'
        }
    }
    assign_warehouse.verbose_name = _('Assign warehouse')

    @transition_action
    def unassign_licences(self, **kwargs):
        BaseObjectLicence.objects.filter(base_object=self).delete()
    unassign_licences.verbose_name = _('Unassign licences')

    @transition_action
    def change_hostname(self, **kwargs):
        country_id = kwargs['country']
        country_name = Country.name_from_id(int(country_id)).upper()
        iso3_country_name = iso2_to_iso3(country_name)
        template_vars = {
            'code': self.model.category.code,
            'country_code': iso3_country_name,
        }
        self.generate_hostname(template_vars=template_vars)

    change_hostname.form_fields = {
        'country': {
            'field': forms.ChoiceField(
                label=_('Country'),
                choices=Country(),
            )
        }
    }
    change_hostname.verbose_name = _('Change hostname')

    @transition_action
    def change_user_and_owner(self, **kwargs):
        UserModel = get_user_model()  # noqa
        user_id = kwargs.get('user', None)
        user = UserModel.objects.get(id=user_id)
        owner_id = kwargs.get('owner', None)
        self.user = user
        if not owner_id:
            self.owner = user
        else:
            self.owner = UserModel.objects.get(id=owner_id)
        self.location = user.location

    change_user_and_owner.form_fields = {
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
    change_user_and_owner.verbose_name = _('Change user and owner')

    def _generate_report(self, name, request):
        report = Report.objects.get(name=name)
        template = report.templates.filter(default=True).first()
        template_content = ''
        with open(template.template.path, 'rb') as f:
            template_content = f.read()

        service_pdf = ExternalService('PDF')
        result = service_pdf.run(
            template=template_content,
            data={
                'id': self.id,
                'logged_user': obj_to_dict(request.user),
                'affected_user': obj_to_dict(self.user),
                'assets': [{
                    'sn': self.sn,
                    'model': str(self.model),
                    'office_info': {'imei': self.imei}
                }]
            }
        )
        output_path = os.path.join(
            tempfile.gettempdir(), '{}-{}.pdf'.format(
                self.user.get_full_name().lower().replace(' ', '-'),
                self.pk
            )
        )
        with open(output_path, 'wb') as f:
            f.write(result)
        return add_attachment_from_disk(
            self, output_path, request.user,
            _('Document autogenerated by {} transition.').format(name)
        )

    @transition_action
    def release_report(self, request, **kwargs):
        attachment = self._generate_report(name='release', request=request)
        attachment.description = kwargs.get('comment', '')
        attachment.save()
        return attachment
    release_report.return_attachment = True
    release_report.form_fields = {
        'comment': {
            'field': forms.CharField(
                label=_('Description'),
                widget=forms.TextInput()
            )
        }
    }
    release_report.verbose_name = _('Release report')

    @transition_action
    def return_report(self, request, **kwargs):
        self._generate_report(name='return', request=request)
    return_report.return_attachment = True
    return_report.verbose_name = _('Return report')


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
