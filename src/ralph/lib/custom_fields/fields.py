import operator
from collections import defaultdict
from functools import reduce
from typing import Any

from django.contrib.contenttypes.fields import (
    create_generic_related_manager,
    GenericRelation
)
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.fields.related import OneToOneRel

from ralph.admin.helpers import get_field_by_relation_path, getattr_dunder


class CustomFieldsWithInheritanceRelation(GenericRelation):
    """
    Relation for custom fields which handle inheritance of custom fields values
    from dependent models (fields) specified in custom_fields_inheritance.

    To use inheritance of custom fields, define `custom_fields_inheritance`
    in your model, specifying paths of fields from which `CustomFieldValue`s
    should be inherited. `custom_fields_inheritance` supports dunder convention
    for nested fields.

    Example:
    class Restaurant(models.Model):
        city = models.ForeignKey(City)

        custom_fields = CustomFieldsWithInheritanceRelation(CustomFieldValue)
        custom_fields_inheritance = OrderedDict([
            ('city', 'City'),
            ('city__country', 'Country'),
        ])

    The priority of inheritance is as follows:
    * the `CustomFieldValue`s (CFVs) set directyl on object has the highest
      priority
    * then CFVs set on first field on `custom_fields_inheritance` list,
      then on second field on that list and so on

    For the example above the priority is as follows:
    * restaurant (highest)
    * restaurant.city
    * restaurant.city.country (lowest)
    """
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # use ReverseGenericRelatedObjectsWithInheritanceDescriptor
        # instead of ReverseGenericRelatedObjectsDescriptor
        setattr(
            cls,
            self.name,
            ReverseGenericRelatedObjectsWithInheritanceDescriptor(
                self,
                self.for_concrete_model
            )
        )


def _get_content_type_from_field_path(model, field_path):
    # TODO: add some validator for it
    # TODO: store fields in some field in meta, not "calculate"
    # it every time
    field = get_field_by_relation_path(model, field_path)
    if isinstance(field, OneToOneRel):
        related_model = field.related_model
    else:
        related_model = field.remote_field.model
    content_type = ContentType.objects.get_for_model(related_model)
    return content_type


def _prioritize_custom_field_values(objects, model, content_type):
    """
    Sort custom field values by priorities and leave the ones with
    biggest priority for each custom field type.

    Priority is defined as follows:
    * the biggest priority has custom field defined directly for
      instance
    * then next priority has CFV from first field on
      `custom_fields_inheritance` list, then second from this list and
      so on
    """
    ct_priority = [content_type.id]
    for field_path in model.custom_fields_inheritance:
        content_type = _get_content_type_from_field_path(model, field_path)
        ct_priority.append(content_type.id)
    ct_priority = {
        ct_id: index for (index, ct_id) in enumerate(ct_priority)
    }
    custom_fields_seen = set()
    for cfv in sorted(
        objects, key=lambda cfv: ct_priority[cfv.content_type_id]
    ):
        if cfv.custom_field_id in custom_fields_seen:
            continue
        custom_fields_seen.add(cfv.custom_field_id)
        yield cfv.id, cfv


class CustomFieldValueQuerySet(models.QuerySet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prioritize = False
        self._prioritize_model_or_instance = None

    def _clone(self):
        clone = super()._clone()
        clone._prioritize = self._prioritize
        clone._prioritize_model_or_instance = self._prioritize_model_or_instance
        return clone

    def prioritize(self, model_or_instance):
        self._prioritize = True
        self._prioritize_model_or_instance = model_or_instance
        return self

    def __iter__(self):
        if self._prioritize:
            # set if to False to not fall into recursion when calling
            # `_prioritize_custom_field_values`
            self._prioritize = False
            for cfv_id, cfv in _prioritize_custom_field_values(
                self,
                self._prioritize_model_or_instance,
                ContentType.objects.get_for_model(
                    self._prioritize_model_or_instance
                )
            ):
                yield cfv
            return
        yield from super().__iter__()

    def values(self, *fields):
        # TODO: handle values and values_list (need to overwrite `iterator`
        # using prioritizing)
        raise NotImplementedError(
            'CustomField queryset does not support values queryset'
        )

    def values_list(self, *fields):
        raise NotImplementedError(
            'CustomField queryset does not support values list queryset'
        )


class RelModel:
    def __init__(self, model: Any, field: CustomFieldsWithInheritanceRelation):
        self.model = model
        self.field = field


class ReverseGenericRelatedObjectsWithInheritanceDescriptor:
    def __init__(self, field, for_concrete_model=True):
        """
        imported from ReverseGenericRelatedObjectsDescriptor
        """
        self.field = field
        self.for_concrete_model = for_concrete_model

    def __get__(self, instance, instance_type=None):
        """
        Overwrite of ReverseGenericRelatedObjectsDescriptor's __get__

        The only difference is calling another (custom) function to get
        RelatedManager, which properly handles inheritance of custom fields
        """
        if instance is None:
            return self
        rel_model = RelModel(model=self.field.remote_field.model, field=self.field)
        # difference here comparing to Django!
        superclass = rel_model.model.inherited_objects.__class__
        RelatedManager = create_generic_related_manager_with_inheritance(
            superclass, rel_model
        )

        manager = RelatedManager(
            instance=instance,
        )

        return manager


def create_generic_related_manager_with_inheritance(superclass, rel):  # noqa: C901
    """
    Extension to Django's create_generic_related_manager.

    Differences:
    * overwrite `get_queryset` to properly handle fetching custom fields for
    single object
    * overwrite `get_prefetch_queryset` to properly prefetch custom fields
    with inheritance  of more than one instance
    """
    # get Django's GenericRelatedObject manager first
    manager = create_generic_related_manager(superclass, rel)

    class GenericRelatedObjectWithInheritanceManager(manager):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # don't use filters for single content type and single object id,
            # like in Django's GenericRelatedObject
            self.core_filters = {}
            # construct inheritance filters based on
            # `custom_fields_inheritance` defined on model
            self.inheritance_filters = [
                self._get_inheritance_filters_for_single_instance()
            ]

        def _get_inheritance_filters_for_single_instance(self):
            """
            Return queryset filter for CustomFieldValue with inheritance for
            single instance.

            Final format of queryset will look similar to:
            (Q(content_type_id=X) & Q(object_id=Y)) | (Q(content_type_id=A) & Q(object_id=B)) | ...  # noqa
            """
            inheritance_filters = [
                # custom field of instance
                models.Q(**{
                    self.content_type_field_name: self.content_type.id
                }) &
                # object id of instance
                models.Q(**{
                    self.object_id_field_name: self.instance.id
                })
            ]
            # for each related field (foreign key), add it's content_type
            # and object_id to queryset filter
            for field_path in self.instance.custom_fields_inheritance:
                content_type = _get_content_type_from_field_path(
                    self.instance, field_path
                )
                value = getattr_dunder(self.instance, field_path)
                # filter only if related field has some value
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
                ).prioritize(self.instance)

        def get_prefetch_queryset(self, instances, queryset=None):
            """
            Prefetch custom fields with inheritance of values for multiple
            instances.

            This implementation is one-big-workaround for Django's handling of
            prefetch_related (especially in
            django.db.models.query:prefetch_one_level)
            """
            if queryset is None:
                queryset = super().get_queryset().select_related(
                    'custom_field'
                )

            queryset._add_hints(instance=instances[0])
            queryset = queryset.using(queryset._db or self._db)
            content_type = ContentType.objects.get_for_model(
                instances[0]
            )
            # store possible content types of CustomFieldValue
            content_types = set([content_type])
            # store possible values of object id
            objects_ids = set()
            # mapping from instance id to content_type and object id of
            # dependent fields for inheritance
            instances_cfs = defaultdict(set)
            # process every instance (no inheritance here right now)
            for instance in instances:
                objects_ids.add(instance.pk)
                instances_cfs[instance.pk].add((content_type.pk, instance.pk))
            # process each dependent field from `custom_fields_inheritance`
            for field_path in self.instance.custom_fields_inheritance:
                # assume that field is foreign key
                content_type = _get_content_type_from_field_path(
                    self.instance, field_path
                )
                content_types.add(content_type)
                # for each instance, get value of this dependent field
                for instance in instances:
                    value = getattr_dunder(instance, field_path)
                    if value:
                        objects_ids.add(value.pk)
                        # store mapping from instance to content type and value
                        # of dependent field to know, which CustomFieldValue
                        # assign later to instance
                        instances_cfs[instance.pk].add(
                            (content_type.pk, value.pk)
                        )

            # filter by possible content types and objects ids
            # notice that thus this filter is not perfect (filter separately
            # for content types and for objects ids, without correlation
            # between particular content type and value), this simplify
            # (and speedup) query
            # alternative solution is to do something similar to fetching
            # custom fields for single instance: correlate content type with
            # possible values for this single content type, for example:
            # (Q(content_type_id=A) & Q(object_id__in=[B, C, D])) | (Q(content_type_id=X) & Q(object_id__in=[Y, Z])) | ... # noqa
            query = {
                '%s__in' % self.content_type_field_name: content_types,
                '%s__in' % self.object_id_field_name: set(objects_ids)
            }

            qs = list(queryset.filter(**query))

            # this fragment of code (at least similar one) is normally done in
            # Django's `prefetch_one_level`, but it does NOT handle M2M case
            # (that single prefetched object (in this case CustomFieldValue)
            # could be assigned to multiple instances - it works only with
            # many-to-one case)

            # mapping from content_type and object_id to `CustomFieldValue`s
            rel_obj_cache = defaultdict(list)
            for rel_obj in qs:
                rel_obj_cache[
                    (rel_obj.content_type_id, rel_obj.object_id)
                ].append(
                    rel_obj
                )

            # for each instance reconstruct it's CustomFieldValues
            # using `instances_cfs` mapping (from instance pk to content_type
            # and object_id of possible CustomFieldValue)
            for obj in instances:
                vals = []
                # fetch `CustomFieldsValue`s for this instance - use mapping
                # from instance pk to content type id and object id of it's
                # dependent fields
                for content_type_id, obj_id in instances_cfs[obj.id]:
                    try:
                        vals.extend(rel_obj_cache[
                            (content_type_id, obj_id)
                        ])
                    except KeyError:
                        # ignore if there is no CustomFieldValue for such
                        # content_type_id and object_id
                        pass
                vals = [
                    v[1] for v in _prioritize_custom_field_values(
                        vals, self.instance, self.content_type
                    )
                ]

                # store `CustomFieldValue`s of instance in cache
                instance_custom_fields_queryset = obj.custom_fields.all()
                instance_custom_fields_queryset._result_cache = vals
                instance_custom_fields_queryset._prefetch_done = True
                obj._prefetched_objects_cache[
                    self.prefetch_cache_name
                ] = instance_custom_fields_queryset

            # main "hack" for Django - since all querysets are already
            # prefetched, `prefetch_one_level` has nothing to do, thus
            # `rel_obj_attr` and `instance_attr` (second and third item)
            # returns constant value, to not assign it to any object.
            return (
                qs,
                lambda relobj: None,
                lambda obj: -1,
                # most important part of this workaround - return single=True,
                # to force `prefetch_one_level` to just do setattr to instance
                # under returned cache_name (suffixed with '__empty' below)
                True,
                # cache_name is also changed to not assign empty result
                # to `custom_fields` (and overwrite prefetched custom fields
                # assigned above)
                self.prefetch_cache_name + '__empty',
                True
            )

    return GenericRelatedObjectWithInheritanceManager
