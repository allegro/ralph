import logging

import six
from dj.choices import Choices
from django import forms
from django.contrib.auth.models import Group
from django.contrib.contenttypes import fields
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.fields.related import lazy_related_operation
from django.utils.text import capfirst, slugify
from django.utils.translation import ugettext_lazy as _

from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin

from .fields import (
    CustomFieldsWithInheritanceRelation,
    CustomFieldValueQuerySet
)

logger = logging.getLogger(__name__)

CUSTOM_FIELD_VALUE_MAX_LENGTH = 1000

STRING_CHOICE = Choices.Choice('string').extra(
    form_field=forms.CharField,
)
INTEGER_CHOICE = Choices.Choice('integer').extra(
    form_field=forms.IntegerField,
)
DATE_CHOICE = Choices.Choice('date').extra(
    form_field=forms.DateField,
)
URL_CHOICE = Choices.Choice('url').extra(
    form_field=forms.URLField,
)
CHOICE_CHOICE = Choices.Choice('choice list').extra(
    form_field=forms.ChoiceField,
)


class CustomFieldTypes(Choices):
    _ = Choices.Choice

    STRING = STRING_CHOICE
    INTEGER = INTEGER_CHOICE
    DATE = DATE_CHOICE
    URL = URL_CHOICE
    CHOICE = CHOICE_CHOICE


class CustomField(AdminAbsoluteUrlMixin, TimeStampMixin, models.Model):
    name = models.CharField(max_length=255, unique=True)
    attribute_name = models.SlugField(
        max_length=255, editable=False, unique=True,
        help_text=_("field name used in API. It's slugged name of the field"),
        db_index=True,
    )
    type = models.PositiveIntegerField(
        choices=CustomFieldTypes(), default=CustomFieldTypes.STRING.id
    )
    choices = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('choices'),
        help_text=_('available choices for `choices list` separated by |'),
    )
    default_value = models.CharField(
        max_length=CUSTOM_FIELD_VALUE_MAX_LENGTH,
        help_text=_('for boolean use "true" or "false"'),
        null=True,
        blank=True,
        default='',
    )
    managing_group = models.ForeignKey(
        Group, blank=True, null=True,
        help_text=_(
            "When set, only members of the specified group will be "
            "allowed to set, change or unset values of this custom field "
            "for objects."
        ), on_delete=models.CASCADE
    )
    use_as_configuration_variable = models.BooleanField(
        default=False,
        help_text=_(
            'When set, this variable will be exposed in API in '
            '"configuration_variables" section. You could use this later in '
            'configuration management tool like Puppet or Ansible.'
        )
    )
    # TODO: when required, custom validator (regex?), is_unique

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.attribute_name = slugify(self.name).replace('-', '_')
        super().save(*args, **kwargs)

    def _get_choices(self):
        if self.type in (
            CustomFieldTypes.CHOICE,
        ):
            return self.choices.split('|')
        return []

    def get_form_field(self):
        params = {
            'initial': self.default_value,
        }
        field_type = CustomFieldTypes.from_id(self.type)
        if issubclass(field_type.form_field, forms.ChoiceField):
            choices = self._get_choices()
            params.update({
                'choices': zip(choices, choices),
            })
        else:
            params.update({
                'required': False
            })
        return field_type.form_field(**params)


class CustomFieldValue(TimeStampMixin, models.Model):
    custom_field = models.ForeignKey(
        CustomField, verbose_name=_('key'), on_delete=models.PROTECT
    )
    # value is stored in charfield on purpose - ralph's custom field mechanism
    # is by-design simple, so it, for example, doesn't allow to filter by range
    # of integers or other Django filters like gte, lte.
    value = models.CharField(max_length=CUSTOM_FIELD_VALUE_MAX_LENGTH)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    object = fields.GenericForeignKey('content_type', 'object_id')

    objects = models.Manager()
    # generic relation has to use specific manager (queryset)
    # which handle inheritance
    inherited_objects = CustomFieldValueQuerySet.as_manager()

    class Meta:
        unique_together = ('custom_field', 'content_type', 'object_id')

    def __str__(self):
        return '{} ({}): {}'.format(
            self.custom_field if self.custom_field_id else None,
            self.object,
            self.value
        )

    def _get_unique_checks(self, exclude=None):
        if exclude:
            for k in ['content_type', 'object_id']:
                try:
                    exclude.remove(k)
                except ValueError:
                    pass
        return super()._get_unique_checks()

    def unique_error_message(self, model_class, unique_check):
        """
        Return better unique validation message than standard Django message.
        """
        opts = model_class._meta

        params = {
            'model': self,
            'model_class': model_class,
            'model_name': six.text_type(capfirst(opts.verbose_name)),
            'unique_check': unique_check,
        }

        if len(unique_check) > 1:
            return ValidationError(
                message=_(
                    "Custom field of the same type already exists for this object."  # noqa
                ),
                code='unique_together',
                params=params,
            )
        return super().unique_error_message(self, model_class, unique_check)

    def clean(self):
        if self.custom_field_id:
            self.custom_field.get_form_field().clean(self.value)
        super().clean()


class CustomFieldMeta(models.base.ModelBase):
    def __new__(cls, name, bases, attrs):
        new_cls = super().__new__(cls, name, bases, attrs)
        new_cls._meta.custom_fields_inheritance_by_model = {}
        new_cls._meta.custom_fields_inheritance_by_path = {}
        # for each field in custom field inheritance, call
        # `add_custom_field_inheritance` - it will be called lazy, only when
        # model will be loaded
        for field_path, model in new_cls.custom_fields_inheritance.items():
            def function(local, related, field):
                return add_custom_field_inheritance(field, related, local)

            lazy_related_operation(function, new_cls, model, field=field_path)
        return new_cls


def add_custom_field_inheritance(field_path, model, cls):
    model._meta.custom_fields_inheritance_by_model[cls] = field_path
    cls._meta.custom_fields_inheritance_by_path[field_path] = cls


class WithCustomFieldsMixin(models.Model, metaclass=CustomFieldMeta):
    # TODO: handle polymorphic in filters
    custom_fields = CustomFieldsWithInheritanceRelation(CustomFieldValue)
    # mapping from field path (using Django __ convention) to model (provided
    # as string location of app_label and model name)
    custom_fields_inheritance = {}

    class Meta:
        abstract = True

    @property
    def custom_fields_as_dict(self):
        return {
            cfv.custom_field.name: cfv.value
            for cfv in self.custom_fields.select_related('custom_field')
        }

    @property
    def custom_fields_configuration_variables(self):
        return {
            cfv.custom_field.name: cfv.value
            for cfv in self.custom_fields.filter(
                custom_field__use_as_configuration_variable=True
            ).select_related('custom_field')
        }

    def update_custom_field(self, name, value):
        cf = CustomField.objects.get(name=name)
        cfv, _ = self.custom_fields.get_or_create(custom_field=cf)
        cfv.value = value
        cfv.save(update_fields=['value'])

    def clear_children_custom_field_value(self, custom_field):
        """
        For each model inheriting `custom_field` from self (in practice
        for each model inheriting, which have this custom_field set to any
        value), delete their `CustomFieldValue`s.
        """
        for model, field_path in self._meta.custom_fields_inheritance_by_model.items():  # noqa: E501
            custom_fields_values_to_delete = CustomFieldValue.objects.filter(
                custom_field=custom_field,
                content_type=ContentType.objects.get_for_model(model),
                object_id__in=model._default_manager.filter(
                    **{field_path: self}
                ).values_list('pk', flat=True),
            )
            logger.warning(
                'Deleting %s CFVs for descendants of %s (%s by %s)',
                custom_fields_values_to_delete.count(), self,
                model, field_path
            )
            custom_fields_values_to_delete.delete()
