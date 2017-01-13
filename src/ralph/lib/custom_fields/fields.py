import operator
from collections import defaultdict
from functools import reduce

from django.contrib.contenttypes.fields import (
    create_generic_related_manager,
    GenericRelation,
    ReverseGenericRelatedObjectsDescriptor
)
from django.contrib.contenttypes.models import ContentType
from django.db import connection, models

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
        custom_fields_inheritance = ['city', 'city__country']
    """
    def contribute_to_class(self, cls, name, **kwargs):
        super().contribute_to_class(cls, name, **kwargs)
        # use ReverseGenericRelatedWithInheritanceObjectsDescriptor
        # instead of ReverseGenericRelatedObjectsDescriptor
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
        """
        Overwrite of ReverseGenericRelatedObjectsDescriptor's __get__

        The only difference is calling another (custom) function to get
        RelatedManager, which properly handles inheritance of custom fields
        """
        if instance is None:
            return self
        rel_model = self.field.rel.to
        superclass = rel_model._default_manager.__class__
        # difference here comparing to Django!
        RelatedManager = create_generic_related_manager_with_iheritance(
            superclass
        )

        qn = connection.ops.quote_name
        content_type = ContentType.objects.db_manager(
            instance._state.db
        ).get_for_model(
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


def create_generic_related_manager_with_iheritance(superclass):  # noqa: C901
    """
    Extension to Django's create_generic_related_manager.

    Differences:
    * overwrite `get_queryset` to properly handle fetching custom fields for
    single object
    * overwrite `get_prefetch_queryset` to properly prefetch custom fields
    with inheritance  of more than one instance
    """
    # get Django's GenericRelatedObject manager first
    manager = create_generic_related_manager(superclass)

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
                # TODO: add some validator for it
                field = get_field_by_relation_path(self.instance, field_path)
                content_type = ContentType.objects.get_for_model(field.rel.to)
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

        def _prioretitize_custom_field_values(self, qs):
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
            ct_priority = [self.content_type.id]
            for field_path in self.instance.custom_fields_inheritance:
                field = get_field_by_relation_path(self.instance, field_path)
                content_type = ContentType.objects.get_for_model(field.rel.to)
                ct_priority.append(content_type.id)
            ct_priority = {
                ct_id: index for (index, ct_id) in enumerate(ct_priority)
            }
            custom_fields_seen = set()
            custom_fields_values_ids = set()
            result = []
            for cfv in sorted(
                qs, key=lambda cfv: ct_priority[cfv.content_type_id]
            ):
                if cfv.custom_field_id in custom_fields_seen:
                    continue
                custom_fields_seen.add(cfv.custom_field_id)
                custom_fields_values_ids.add(cfv.id)
                result.append(cfv)
            return custom_fields_values_ids, result

        def get_queryset(self):
            try:
                return self.instance._prefetched_objects_cache[
                    self.prefetch_cache_name
                ]
            except (AttributeError, KeyError):
                super_qs = super().get_queryset()
                qs = super_qs.filter(
                    *self.inheritance_filters
                )
                custom_field_values_ids = (
                    self._prioretitize_custom_field_values(qs)[0]
                )
                return super_qs.filter(pk__in=custom_field_values_ids)

        def get_prefetch_queryset(self, instances, queryset=None):
            """
            Prefetch custom fields with inheritance of values for multiple
            instances.

            This implementation is one-big-workaround for Django's handling of
            prefetch_related (especially in
            django.db.models.query:prefetch_one_level)
            """
            if queryset is None:
                queryset = super().get_queryset()

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
                field = get_field_by_relation_path(self.instance, field_path)
                content_type = ContentType.objects.get_for_model(field.rel.to)
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

                vals = self._prioretitize_custom_field_values(vals)[1]

                # store `CustomFieldValue`s of instance in cache
                instance_custom_fields_queryset = getattr(
                    obj, 'custom_fields'
                ).all()
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
                self.prefetch_cache_name + '__empty'
            )

    return GenericRelatedObjectWithInheritanceManager
