import six

from dj.choices import Choices
from django import forms
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import capfirst, slugify
from django.utils.translation import ugettext_lazy as _

from ralph.lib.mixins.models import TimeStampMixin

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
BOOLEAN_CHOICE = Choices.Choice('boolean').extra(
    form_field=forms.BooleanField,
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
    BOOLEAN = BOOLEAN_CHOICE
    URL = URL_CHOICE
    CHOICE = CHOICE_CHOICE


class CustomField(TimeStampMixin, models.Model):
    name = models.CharField(max_length=255, unique=True)
    attribute_name = models.SlugField(
        max_length=255, editable=False, unique=True
    )
    type = models.PositiveIntegerField(
        choices=CustomFieldTypes(), default=CustomFieldTypes.STRING.id
    )
    choices = models.CharField(
        max_length=1024,
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
    # TODO: when required, custom validator (regex?), is_unique

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.attribute_name = slugify(self.name).replace('-', '_')
        super().save(*args, **kwargs)

    def _get_choices(self):
        assert self.type in (
            CustomFieldTypes.CHOICE,
        )
        return self.choices.split('|')

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
        return field_type.form_field(**params)


class CustomFieldValue(TimeStampMixin, models.Model):
    custom_field = models.ForeignKey(CustomField, verbose_name=_('key'))
    # value is stored in charfield on purpose - ralph's custom field mechanism
    # is by-design simple, so it, for example, don't allow to filter by range
    # of integers or other Django filters like gte, lte.
    value = models.CharField(max_length=CUSTOM_FIELD_VALUE_MAX_LENGTH)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    object = generic.GenericForeignKey('content_type', 'object_id')

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


class WithCustomFieldsMixin(models.Model):
    custom_fields = GenericRelation(CustomFieldValue)

    class Meta:
        abstract = True
