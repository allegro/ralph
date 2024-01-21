# -*- coding: utf-8 -*-
"""
Polymorphic using inherited models in Django.
Displays information in queryset list about the model that inherits
the polymorphic model

Example:
    >>>  Model.polymorphic_objects.all()
    [
        <Model1: model1: test>,
        <Model2: model2: test>,
        <Model3: model3: test>
    ]
"""
from collections import defaultdict
from itertools import groupby

from django.contrib.contenttypes.models import ContentType
from django.db import models, OperationalError

from ralph.lib.error_handling.exceptions import WrappedOperationalError


class PolymorphicQuerySet(models.QuerySet):
    def __init__(self, *args, **kwargs):
        self._polymorphic_select_related = {}
        self._polymorphic_prefetch_related = {}
        self._annotate_args = []
        self._annotate_kwargs = {}
        self._extra_args = []
        self._extra_kwargs = {}
        self._polymorphic_filter_args = []
        self._polymorphic_filter_kwargs = {}
        super().__init__(*args, **kwargs)

    def iterator(self):
        """
        Override iterator:
            - Iterate for all objects and collected ID
            - For each ContentType generates additional queryset
            - Returns iterator with different models
        """
        # if this is final-level model, don't check for descendants - just
        # return original queryset result
        if not getattr(self.model, '_polymorphic_descendants', []):
            yield from super().iterator()
            return

        result = []
        content_types_ids = set()
        select_related = None
        if self.query.select_related:
            select_related = self.query.select_related
            self.query.select_related = False

        for obj in super().iterator():
            content_types_ids.add(obj.content_type_id)
            result.append((
                obj.content_type_id, obj.pk)
            )
        # store original order of items by PK
        pks_order = [r[1] for r in result]
        # WARNING! sorting result (by content type) breaks original order of
        # items - we need to restore it at the end of this function
        result = groupby(sorted(result), lambda x: x[0])

        content_type_model_map = {
            ct.id: ct.model_class() for ct in ContentType.objects.filter(
                pk__in=list(content_types_ids)
            )
        }
        # NOTICE: there might be multiple objects with the same ct_id and
        # pk!! (ex. because of filters causing joins - ex. for prefetch related,
        # when one object is attached to many others). We need to group them
        # and return all of them (order is rather irrelevant then, because
        # it's the same object).
        result_mapping = defaultdict(list)
        for k, v in result:
            model = content_type_model_map[k]
            polymorphic_models = getattr(model, '_polymorphic_models', [])
            if polymorphic_models and model not in polymorphic_models:
                model_query = model.objects.filter(pk__in=[i[1] for i in v])
                model_name = model._meta.object_name
                # first check if select_related/prefetch_related is present for
                # this model to not trigger selecting/prefetching all related
                # or reset select_related accidentally
                # see https://docs.djangoproject.com/en/1.8/ref/models/querysets/#select-related  # noqa
                # for details
                if select_related:
                    model_query.query.select_related = select_related.copy()

                if self._polymorphic_select_related.get(model_name):
                    model_query = model_query.select_related(
                        *self._polymorphic_select_related[model_name]
                    )
                if self._polymorphic_prefetch_related.get(model_name):
                    model_query = model_query.prefetch_related(
                        *self._polymorphic_prefetch_related[model_name]
                    )
                model_query = model_query.annotate(
                    *self._annotate_args, **self._annotate_kwargs
                ).extra(*self._extra_args, **self._extra_kwargs)

                # rewrite filters to properly handle joins between tables
                # TODO(mkurek): handle it better since it will produce
                # additional (unnecessary) WHERE conditions. Consider for
                # example extracting (somehow) joined tables from filter
                # fields and put them into `select_related`
                if (
                    self._polymorphic_filter_args or
                    self._polymorphic_filter_kwargs
                ):
                    model_query = model_query.filter(
                        *self._polymorphic_filter_args,
                        **self._polymorphic_filter_kwargs
                    )
                try:
                    for obj in model_query:
                        result_mapping[obj.pk].append(obj)
                # NOTE(pszulc): We try to catch OperationalError that randomly
                # occurs (1052, "Column 'created' in field list is ambiguous")
                except OperationalError as e:
                    raise WrappedOperationalError(
                        query=model_query.query, model=self, error_str=str(e)) \
                        from e
        # yield objects in original order
        for pk in pks_order:
            # yield all objects with particular PK
            # it might happen that there will be additional objects with
            # particular PK comparing to original query. This might happen when
            # "broad" polymorphic_filter is used with prefetch_related (and
            # original model is filtered to get only subset of all objects)
            # see test cases in `PolymorphicTestCase` for examples.
            while result_mapping[pk]:
                yield result_mapping[pk].pop()

    def annotate(self, *args, **kwargs):
        self._annotate_args.extend(args)
        self._annotate_kwargs.update(kwargs)
        return super().annotate(*args, **kwargs)

    def extra(self, *args, **kwargs):
        self._extra_args.extend(args)
        self._extra_kwargs.update(kwargs)
        return super().extra(*args, **kwargs)

    def _clone(self, *args, **kwargs):
        clone = super()._clone(*args, **kwargs)
        clone._polymorphic_select_related = (
            self._polymorphic_select_related.copy()
        )
        clone._polymorphic_prefetch_related = (
            self._polymorphic_prefetch_related.copy()
        )
        clone._annotate_kwargs = (
            self._annotate_kwargs.copy()
        )
        clone._annotate_args = (
            self._annotate_args.copy()
        )
        clone._extra_args = self._extra_args.copy()
        clone._extra_kwargs = self._extra_kwargs.copy()
        clone._polymorphic_filter_args = self._polymorphic_filter_args.copy()
        clone._polymorphic_filter_kwargs = (
            self._polymorphic_filter_kwargs.copy()
        )
        return clone

    def polymorphic_select_related(self, **kwargs):
        """
        Apply select related on descendant model (passed as model name). Usage:

        >>> MyBaseModel.objects.polymorphic_select_related(
            MyDescendantModel=['related_field1', 'related_field2'],
            MyDescendantModel2=['related_field3'],
        )
        """
        obj = self._clone()
        obj._polymorphic_select_related = kwargs
        return obj

    def polymorphic_prefetch_related(self, **kwargs):
        """
        Apply prefetch related on descendant model (passed as model name).
        Usage:

        >>> MyBaseModel.objects.polymorphic_prefetch_related(
            MyDescendantModel=['related_field1', 'related_field2'],
            MyDescendantModel2=['related_field3'],
        )
        """
        obj = self._clone()
        obj._polymorphic_prefetch_related = kwargs
        return obj

    def polymorphic_filter(self, *args, **kwargs):
        """
        Extra filter for descendat model

        Might be useful (as a workaround) for forcing join on descendant model
        in some cases with prefetch_related with queryset with polymorphic
        objects.
        """
        obj = self._clone()
        obj._polymorphic_filter_args.extend(args)
        obj._polymorphic_filter_kwargs.update(kwargs)
        return obj


class PolymorphicBase(models.base.ModelBase):

    """
    Looking for classes in all classes that inherit from class polymorphic.

    Adding:
        - polymorphic models to class as attributes
        - polymorphic descendants to bases class as attributes
        - set is_polymorphic flag to bases class if class is polymorphic
    """

    def __new__(cls, name, bases, attrs):
        full_mro = set(
            tuple([mro for b in bases for mro in b.__mro__]) + bases
        )
        base_polymorphic = set(
            [b for b in full_mro if issubclass(b, Polymorphic)]
        )
        attrs['_polymorphic_descendants'] = []
        attrs['_polymorphic_models'] = base_polymorphic
        new_class = super().__new__(cls, name, bases, attrs)
        for polymorphic_class in base_polymorphic:
            # Set is_polymorphic flag for classes that use polymorphic
            polymorphic_class.is_polymorphic = True
            if new_class._meta.proxy:
                continue
            try:
                polymorphic_class._polymorphic_descendants.append(new_class)
            except AttributeError:
                # The exception is for class Polymorphic
                pass
        return new_class


class Polymorphic(models.Model):

    """
    Polymorphic model.

    Added content type field to model

    Example:
        >>> class Test(Polymorphic, models.Model, metaclass=PolymorphicBase):
                pass
    """

    content_type = models.ForeignKey(ContentType, blank=True, null=True)

    polymorphic_objects = PolymorphicQuerySet.as_manager()
    objects = models.Manager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        """
        Save object content type
        """
        if not self.content_type:
            self.content_type = ContentType.objects.get_for_model(self)
        super().save(*args, **kwargs)

    @property
    def last_descendant(self):
        return self.content_type.get_object_for_this_type(pk=self.pk)
