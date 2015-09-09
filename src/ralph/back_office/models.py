# -*- coding: utf-8 -*-
import re

from dj.choices import Country
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.forms import ValidationError
from django.utils.translation import ugettext_lazy as _

from ralph.accounts.models import Regionalizable
from ralph.assets.country_utils import iso2_to_iso3
from ralph.assets.models.assets import Asset
from ralph.assets.models.choices import AssetStatus
from ralph.lib.mixins.fields import NullableCharField
from ralph.lib.mixins.models import NamedMixin, TimeStampMixin
from ralph.lib.transitions.decorators import transition_action
from ralph.lib.transitions.fields import TransitionField
from ralph.licences.models import BaseObjectLicence

IMEI_UNTIL_2003 = re.compile(r'^\d{6} *\d{2} *\d{6} *\d$')
IMEI_SINCE_2003 = re.compile(r'^\d{8} *\d{6} *\d$')


class Warehouse(NamedMixin, TimeStampMixin, models.Model):
    pass


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
        default=AssetStatus.new.id,
        choices=AssetStatus(),
    )
    imei = NullableCharField(
        max_length=18, null=True, blank=True, unique=True
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
        return '{}'.format(self.hostname)

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

    @transition_action
    def assign_user(self, **kwargs):
        self.user = get_user_model().objects.get(pk=int(kwargs['user']))

    assign_user.form_fields = {
        'user': {
            'field': forms.CharField(label=_('User')),
            'autocomplete_field': 'user'
        }
    }

    @transition_action
    def assign_owner(self, **kwargs):
        self.owner = get_user_model().objects.get(pk=int(kwargs['owner']))

    assign_owner.form_fields = {
        'owner': {
            'field': forms.CharField(label=_('Owner')),
            'autocomplete_field': 'owner'
        }
    }

    @transition_action
    def unassign_owner(self, **kwargs):
        self.owner = None

    @transition_action
    def unassign_user(self, **kwargs):
        self.user = None

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

    @transition_action
    def unassign_loan_end_date(self, **kwargs):
        self.loan_end_date = None

    @transition_action
    def assign_warehouse(self, **kwargs):
        self.warehouse = Warehouse.objects.get(pk=int(kwargs['warehouse']))

    assign_warehouse.form_fields = {
        'warehouse': {
            'field': forms.CharField(label=_('Warehouse')),
            'autocomplete_field': 'warehouse'
        }
    }

    @transition_action
    def unassign_licences(self, **kwargs):
        BaseObjectLicence.objects.filter(base_object=self).delete()

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
