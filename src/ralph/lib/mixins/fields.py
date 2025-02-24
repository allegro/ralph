# -*- coding: utf-8 -*-
import netaddr
from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.admin.widgets import AdminTextInputWidget
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.forms.utils import flatatt
from django.utils import six
from django.utils.html import format_html, smart_urlquote
from django.utils.translation import ugettext_lazy as _
from taggit.forms import TagField


class NullableFormFieldMixin(object):
    def to_python(self, value):
        """Returns a Unicode object."""
        if value in self.empty_values:
            return None
        return super().to_python(value)


class NullableCharFormField(NullableFormFieldMixin, forms.CharField):
    pass


class NullableGenericIPAddressFormField(
    NullableFormFieldMixin, forms.GenericIPAddressField
):
    pass


class NullableCharFieldMixin(object):
    """
    Mixin for char fields and descendants which will replace empty string value
    ('') by null when saving to the database.

    It's especially useful when field is marked as unique and at the same time
    allows null/blank (`models.CharField(unique=True, null=True, blank=True)`)
    """
    _formfield_class = NullableCharFormField

    def get_prep_value(self, value):
        return super().get_prep_value(value) or None

    def formfield(self, **kwargs):
        defaults = {}
        if self._formfield_class:
            defaults['form_class'] = self._formfield_class
        defaults.update(kwargs)
        return super().formfield(**defaults)


class NullableCharField(
    NullableCharFieldMixin,
    models.CharField,
):
    pass


class NullableCharFieldWithAutoStrip(
    NullableCharField
):
    def clean(self, value, model_instance):
        return super().clean(value.strip(), model_instance)


# NOTE(romcheg): NUMP stands for No Useles Migrations Please.
#                It is recommended to refrain from checking the other meaning
#                in UD.
class NUMPFieldMixIn(object):

    def __init__(self, *args, **kwargs):
        fields_to_ignore = kwargs.pop('fields_to_ignore', None)
        super(NUMPFieldMixIn, self).__init__(*args, **kwargs)
        self.fields_to_ignore = fields_to_ignore if (
            fields_to_ignore is not None
        ) else ('help_text', 'verbose_name')

    def deconstruct(self):
        name, path, args, kwargs = super(NUMPFieldMixIn, self).deconstruct()

        # NOTE(romcheg): Perform arguments substitution only for direct
        #                descendants.
        if not self.__class__.__mro__.index(NUMPFieldMixIn) > 1:
            # NOTE(romcheg): Exclude all fields that should not be concidered
            #                when generating migrations.
            kwargs = {
                f: kwargs[f] for f in kwargs if f not in self.fields_to_ignore
            }
            path = '{}.{}'.format(NUMP.__module__, NUMP.__name__)

            nump_args = [self.base_class(*args, **kwargs)]
            nump_kwargs = {'fields_to_ignore': self.fields_to_ignore}

            return name, path, nump_args, nump_kwargs

        return name, path, args, kwargs


NUMP_FIELD_CACHE = {}


def get_nump_class(base_field, fields_to_ignore):
    global NUMP_FIELD_CACHE
    base_class = base_field.__class__

    cache_lookup = tuple((base_class,) + fields_to_ignore)

    if cache_lookup not in NUMP_FIELD_CACHE:
        nump_field_name = 'NUMP' + base_class.__name__
        NUMP_FIELD_CACHE[cache_lookup] = type(
            nump_field_name,
            (NUMPFieldMixIn, base_class),
            {'base_class': base_class}
        )

    return NUMP_FIELD_CACHE[cache_lookup]


def NUMP(base_field, fields_to_ignore=('help_text', 'verbose_name')):
    """Decorator to avoid migrations when not important fields are changed."""

    klass = get_nump_class(base_field, fields_to_ignore)
    name, path, args, kwargs = base_field.deconstruct()

    kwargs['fields_to_ignore'] = fields_to_ignore

    return klass(*args, **kwargs)


class NullableGenericIPAddressField(
    NullableCharFieldMixin,
    models.GenericIPAddressField
):
    _formfield_class = NullableGenericIPAddressFormField


class TicketIdField(NullableCharField):
    def __init__(
        self,
        verbose_name=_('ticket ID'),
        help_text=_('External system ticket identifier'),
        null=True,
        blank=True,
        max_length=200,
        *args, **kwargs
    ):
        super().__init__(
            verbose_name=verbose_name,
            help_text=help_text,
            null=null,
            blank=blank,
            max_length=max_length,
            *args, **kwargs
        )

    def _strip_issue_tracker_url(self, value):
        """
        Strip (generic) issue tracker url from the beggining if url is
        passed into ticket_id
        """
        if (
            value and
            value.startswith(settings.ISSUE_TRACKER_URL)
        ):
            value = value[len(settings.ISSUE_TRACKER_URL):]
        return value.strip()

    def clean(self, value, model_instance):
        value = self._strip_issue_tracker_url(value)
        return super().clean(value, model_instance)


class TicketIdFieldWidget(AdminTextInputWidget):
    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        if value:
            url = '{}{}'.format(settings.ISSUE_TRACKER_URL, value)
            final_attrs = {'href': smart_urlquote(url), 'target': '_blank'}
            html = format_html(
                '<div class="ticket-url">{}<a{}>{}</a></div>',
                html, flatatt(final_attrs), url,
            )
        return html


class BaseObjectForeignKey(models.ForeignKey):
    """
    Base object Foreign Key.

    Add support for additional parameter `limit_models` for
    Foreign Key field.
    This gives option to limit referenced models (by the BaseObject) to
    models defined by `limit_models`.
    For example, let's say we have BaseObjectLicence which should only pointed
    to:
        - BackOfficeAsset
        - DataCenterAsset

    we could define it like here:
        ```
        class BaseObjectLicence(models.Model):
            licence = models.ForeignKey(Licence)
            base_object = BaseObjectForeignKey(
                BaseObject,
                related_name='licences',
                verbose_name=_('Asset'),
                limit_models=[
                    'back_office.BackOfficeAsset',
                    'data_center.DataCenterAsset'
                ]
            )
        ```
    and from now `BaseObjectLicence.base_object` only gets `BackOfficeAsset` and
    `DataCenterAsset` (and not other models inherited from `BaseObject`).
    """
    def __init__(self, *args, **kwargs):
        self.limit_models = kwargs.pop('limit_models', [])
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Otherwise the migrations won't be created if limit_models changes
        if self.limit_models:
            kwargs['limit_models'] = self.limit_models
        return name, path, args, kwargs

    def limit_choices_to(self):
        return self.limit_choices()

    def get_limit_choices_to(self):
        return self.limit_choices()

    def limit_choices(self):
        """
        Add limit_choices_to search by content_type for models
        inherit Polymorphic
        """
        if self.limit_models:
            content_types = ContentType.objects.get_for_models(
                *[apps.get_model(*i.split('.')) for i in self.limit_models]
            )
            return {'content_type__in': content_types.values()}

        return {}

    def get_limit_models(self):
        """
        Returns Model class list from limit_models.
        """
        return [apps.get_model(model) for model in self.limit_models]


class TagWidget(forms.TextInput):
    def render(self, name, value, attrs=None, renderer=None):
        if value is not None and not isinstance(value, six.string_types):
            value = ', '.join(sorted([
                (t if ',' not in t else '"%s"' % t) for t in value
            ]))
        if attrs is None:
            attrs = {}
        attrs['class'] = 'vTextField'
        return super(TagWidget, self).render(name, value, attrs, renderer)


class TaggitTagField(TagField):
    widget = TagWidget

    def has_changed(self, initial, data):
        """
        Args:
            initial: list of original tags
            data: string with comma-separated tags from form
        Examples:

        >>> has_changed(['a', 'b'], 'a, b')
        False
        >>> has_changed(['a', 'b'], 'a, b, c')
        True
        >>> has_changed(['a', 'b'], 'a')
        True
        >>> has_changed(['a', 'b'], 'b, a')
        False
        """
        if initial and data:
            data = [i.strip() for i in data.split(',') if i.strip()]
            changed = len(initial) != len(data) or set(initial) - set(data)
            return changed
        return initial or data


class RalphMACStrategy(netaddr.mac_unix_expanded):
    word_fmt = '%.2X'


class MACAddressField(NullableCharField):
    dialect = RalphMACStrategy
    default_error_messages = {
        'invalid': _("'%(value)s' is not a valid MAC address."),
    }
    description = 'MAC address'
    max_length = len('aa:aa:aa:aa:aa:aa')

    def __init__(self, verbose_name=None, **kwargs):
        kwargs['max_length'] = self.max_length
        super().__init__(verbose_name, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        del kwargs['max_length']
        return name, path, args, kwargs

    def get_db_prep_value(self, value, connection, prepared=False):
        return self.normalize(value)

    def to_python(self, value):
        try:
            return self.normalize(value)
        except ValueError:
            raise ValidationError(
                self.error_messages['invalid'] % {'value': value},
            )

    @classmethod
    def normalize(cls, value):
        """
        Normalize MAC address to EUI-48 format using unix expanded dialect
        (separated by :).
        """
        if not value:
            return None
        try:
            mac = netaddr.EUI(value, version=48, dialect=cls.dialect)
        except netaddr.AddrFormatError:
            raise ValueError("Invalid MAC address: '{}'".format(value))
        return str(mac) or None
