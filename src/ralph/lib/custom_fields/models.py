import operator
import six
from collections import defaultdict
from functools import reduce

from dj.choices import Choices
from django import forms
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.fields import (
    create_generic_related_manager,
    GenericRelation,
    ReverseGenericRelatedObjectsDescriptor
)
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import connection, models
from django.utils.text import capfirst, slugify
from django.utils.translation import ugettext_lazy as _

from ralph.admin.helpers import get_field_by_relation_path, getattr_dunder
from ralph.lib.mixins.models import AdminAbsoluteUrlMixin, TimeStampMixin

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
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField(db_index=True)
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


class CustomFieldsWithInheritanceRelation(GenericRelation):
    def contribute_to_class(self, cls, name, **kwargs):
        super(GenericRelation, self).contribute_to_class(cls, name, **kwargs)
        setattr(
            cls,
            self.name,
            ReverseGenericRelatedWithInheritanceObjectsDescriptor(
                self,
                self.for_concrete_model
            )
        )


class ReverseGenericRelatedWithInheritanceObjectsDescriptor(
    ReverseGenericRelatedObjectsDescriptor
):
    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self

        # Dynamically create a class that subclasses the related model's
        # default manager.
        rel_model = self.field.rel.to
        superclass = rel_model._default_manager.__class__
        # diff!
        RelatedManager = create_generic_related_manager_with_iheritance(
            superclass
        )

        qn = connection.ops.quote_name
        content_type = ContentType.objects.db_manager(instance._state.db).get_for_model(
            instance, for_concrete_model=self.for_concrete_model)

        join_cols = self.field.get_joining_columns(reverse_join=True)[0]
        manager = RelatedManager(
            model=rel_model,
            instance=instance,
            source_col_name=qn(join_cols[0]),
            target_col_name=qn(join_cols[1]),
            content_type=content_type,
            content_type_field_name=self.field.content_type_field_name,
            object_id_field_name=self.field.object_id_field_name,
            prefetch_cache_name=self.field.attname,
        )

        return manager


def create_generic_related_manager_with_iheritance(superclass):
    manager = create_generic_related_manager(superclass)

    class GenericRelatedObjectWithInheritanceManager(manager):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.core_filters = {}
            self.inheritance_filters = [self._get_inheritance_filters()]

        def _get_inheritance_filters(self):
            inheritance_filters = [
                models.Q(**{
                    self.content_type_field_name: self.content_type.id
                }) &
                models.Q(**{
                    self.object_id_field_name: self.instance.id
                })
            ]
            for field_path in self.instance.custom_fields_inheritance:
                # assume that field is foreign key
                # TODO: add some validator for it
                field = get_field_by_relation_path(self.instance, field_path)
                content_type = ContentType.objects.get_for_model(field.rel.to)
                value = getattr_dunder(self.instance, field_path)
                if value:
                    inheritance_filters.append(
                        models.Q(**{
                            self.content_type_field_name: content_type.id
                        }) &
                        models.Q(**{
                            self.object_id_field_name: value.pk
                        })
                    )
            return reduce(operator.or_, inheritance_filters)

        def get_queryset(self):
            try:
                return self.instance._prefetched_objects_cache[
                    self.prefetch_cache_name
                ]
            except (AttributeError, KeyError):
                return super().get_queryset().filter(
                    *self.inheritance_filters
                )

        def get_prefetch_queryset(self, instances, queryset=None):
            if queryset is None:
                queryset = super().get_queryset()

            queryset._add_hints(instance=instances[0])
            queryset = queryset.using(queryset._db or self._db)
            content_type = ContentType.objects.get_for_model(
                instances[0]
            )
            content_types = set([content_type])
            values = set()
            instances_cfs = defaultdict(set)
            for instance in instances:
                values.add(instance.pk)
                instances_cfs[instance.pk].add((content_type.pk, instance.pk))
            for field_path in self.instance.custom_fields_inheritance:
                # assume that field is foreign key
                # TODO: add some validator for it
                field = get_field_by_relation_path(self.instance, field_path)
                content_type = ContentType.objects.get_for_model(field.rel.to)
                content_types.add(content_type)
                for instance in instances:
                    value = getattr_dunder(instance, field_path)
                    if value:
                        values.add(value.pk)
                        instances_cfs[instance.pk].add(
                            (content_type.pk, value.pk)
                        )

            # not perfect
            query = {
                '%s__in' % self.content_type_field_name: content_types,
                '%s__in' % self.object_id_field_name: set(values)
            }

            qs = list(queryset.filter(**query))
            rel_obj_cache = {}
            for rel_obj in qs:
                rel_obj_cache[(rel_obj.content_type_id, rel_obj.object_id)] = rel_obj

            for obj in instances:
                vals = []
                for rel_obj_ct_id, rel_obj_id in instances_cfs[obj.id]:
                    try:
                        vals.append(rel_obj_cache[(rel_obj_ct_id, rel_obj_id)])
                    except KeyError:
                        pass

                obj_qs = getattr(obj, 'custom_fields').all()
                obj_qs._result_cache = vals
                # We don't want the individual obj_qs doing prefetch_related now,
                # since we have merged this into the current work.
                obj_qs._prefetch_done = True
                obj._prefetched_objects_cache[self.prefetch_cache_name] = obj_qs
            return (
                qs,
                lambda relobj: None,
                lambda obj: -1,
                True,
                self.prefetch_cache_name + '__empty'
            )

    return GenericRelatedObjectWithInheritanceManager


class WithCustomFieldsMixin(models.Model):
    # TODO: handle polymorphic in filters
    custom_fields = CustomFieldsWithInheritanceRelation(CustomFieldValue)
    custom_fields_inheritance = []

    class Meta:
        abstract = True

    @property
    def custom_fields_as_dict(self):
        return dict(self.custom_fields.values_list(
            'custom_field__name', 'value'
        ))

    @property
    def custom_fields_configuration_variables(self):
        return dict(self.custom_fields.filter(
            custom_field__use_as_configuration_variable=True
        ).values_list(
            'custom_field__name', 'value'
        ))

    def update_custom_field(self, name, value):
        cf = CustomField.objects.get(name=name)
        cfv, _ = self.custom_fields.get_or_create(custom_field=cf)
        cfv.value = value
        cfv.save(update_fields=['value'])
