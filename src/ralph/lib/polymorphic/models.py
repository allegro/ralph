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
from typing import Dict, Iterable, List, Tuple

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core import exceptions
from django.db import models
from django.db.models import QuerySet
from django.db.models.base import ModelBase


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
        self._my_cache = None
        self._pks_order = None
        super().__init__(*args, **kwargs)

    def _fetch_all(self):
        if self._result_cache is not None:
            return
        self._result_cache = None
        self._my_cache = None
        self._pks_order = None

        if self.query.select_related:
            self._select_related = self.query.select_related
            self.query.select_related = False
        else:
            self._select_related = None

        super()._fetch_all()
        try:
            self._pks_order = [obj.pk for obj in self._result_cache]  # type: ignore
        except AttributeError:
            return self._result_cache

        result = groupby(
            sorted(self._result_cache, key=lambda x: x.content_type_id),
            lambda x: x.content_type_id,
        )  # type: Iterable[Tuple[int, object]]
        self._my_cache = self._subquery_for_children_models(result)

    def _subquery_for_children_models(self, result) -> Dict[int, List[object]]:
        result_mapping = defaultdict(list)
        for ct_id, objects_of_type in result:
            content_type = ContentType.objects.get_for_id(id=ct_id)
            model = content_type.model_class()
            polymorphic_models = getattr(model, "_polymorphic_models", [])
            if not (polymorphic_models and model not in polymorphic_models):
                continue
            model_name = model._meta.object_name
            ids = {obj.id for obj in objects_of_type}  # type: set[int]
            model_query = model.objects.filter(pk__in=ids)
            model_query = self._add_select_related_to_subquery(model_query)
            model_query = self._add_polymorphic_select_related_to_subquery(
                model_query, model_name
            )
            model_query = self._add_polymorphic_prefetch_related_to_subquery(
                model_query, model_name
            )
            model_query = self._add_polymorphic_filter_to_subquery(model_query)
            model_query = model_query.annotate(
                *self._annotate_args, **self._annotate_kwargs
            )
            model_query = self._add_extra_to_subquery(model_query)

            for obj in model_query:
                result_mapping[obj.pk].append(obj)
        return result_mapping

    def _add_select_related_to_subquery(self, query: QuerySet):
        if self._select_related:
            query.query.select_related = self._select_related.copy()
            return query
        else:
            return query

    def _add_polymorphic_select_related_to_subquery(
        self, query: QuerySet, model_name: str
    ) -> QuerySet:
        if self._polymorphic_select_related.get(model_name):
            return query.select_related(*self._polymorphic_select_related[model_name])
        else:
            return query

    def _add_polymorphic_prefetch_related_to_subquery(
        self, query: QuerySet, model_name: str
    ) -> QuerySet:
        if self._polymorphic_prefetch_related.get(model_name):
            return query.prefetch_related(
                *self._polymorphic_prefetch_related[model_name]
            )
        else:
            return query

    def _add_polymorphic_filter_to_subquery(self, query: QuerySet) -> QuerySet:
        try:
            return query.filter(
                *self._polymorphic_filter_args, **self._polymorphic_filter_kwargs
            )
        except exceptions.FieldError:
            # This is expected
            # if a model doesn't have a field we don't want any object of that type
            return query.none()

    def _add_extra_to_subquery(self, query: QuerySet) -> QuerySet:
        query = query.extra(*self._extra_args, **self._extra_kwargs)
        if (
            self._annotate_args
            or self._annotate_kwargs
            or self._extra_args
            or self._extra_kwargs
        ):
            for select_key, select_db_field in self._iterate_extra_prefetches():
                through_table_name, column_name = [
                    s.strip("`").strip('"') for s in select_db_field.split(".")
                ]
                through_fields = [
                    o for o in self.model._meta.get_fields() if hasattr(o, "through")
                ]
                for through_field in through_fields:
                    if through_field.through._meta.db_table == through_table_name:
                        query = self._add_where_conditions(
                            query, through_field.through, column_name
                        )
        return query

    def _iterate_extra_prefetches(self) -> Iterable[Tuple[str, str]]:
        """
        When making prefetch, select is added to the query
        Key is the name of the attribute to be added to the row
        Value is a `table_name`.`column_name` from where the value will come
        """
        for select_key, select_value in self._extra_kwargs.get("select", {}).items():
            if "_prefetch_related_val_" in select_key:
                yield select_key, select_value

    def _add_where_conditions(
        self, query: QuerySet, through_table: ModelBase, target_column_name: str
    ) -> QuerySet:
        """
        Given a through table we find table and column names to make join
        We know target column name so, assuming through tables aren't handcrafted,
        it's easy to find the rest
        We start with:
        select={
            '_prefetch_related_val_somem2mmodel_id':
                '''`polymorphic_tests_somem2mmodel_polymorphics`.`somem2mmodel_id`'''
        },
        And want to add missing tables and where clauses:
        tables=[
            '`polymorphic_tests_somem2mmodel_polymorphics`',
            '`polymorphic_tests_somem2mmodel`'
        ],
        where=[
            "`polymorphic_tests_somem2mmodel_polymorphics`.`polymorphicmodelbasetest_id` "
            "= `polymorphic_tests_polymorphicmodelbasetest`.`id`",
            "`polymorphic_tests_somem2mmodel_polymorphics`.`somem2mmodel_id` "
            "= `polymorphic_tests_somem2mmodel`.`id`",
        ]
        """

        def get_database_quote_type() -> str:
            db_engine = settings.DATABASES["default"]["ENGINE"]
            if "mysql" in db_engine:
                return "`"
            else:
                return '"'

        # mysql uses different quotes than postgres
        q = get_database_quote_type()
        through_table_name = through_table._meta.db_table  # type: str
        fields = {field for field in through_table._meta.fields}  # type: set[models.Field]
        if target_column_name in {field.column for field in fields}:
            our_table = None  # type: str | None
            back_column = None  # type: str | None
            remote_table = None  # type: str | None

            for field in fields:
                if not field.is_relation:
                    continue
                elif field.column == target_column_name:
                    remote_table = field.related_model._meta.db_table
                else:
                    back_column = field.column
                    our_table = field.related_model._meta.db_table
            if our_table and back_column and remote_table:
                condition_local = f"{q}{our_table}{q}.{q}id{q} = {q}{through_table_name}{q}.{q}{back_column}{q}"
                condition_remote = (
                    f"{q}{remote_table}{q}.{q}id{q}"
                    f" = {q}{through_table_name}{q}.{q}{target_column_name}{q}"
                )
                query = query.extra(
                    tables=[f"{q}{remote_table}{q}", f"{q}{through_table_name}{q}"],
                    where=[condition_local, condition_remote],
                )
        return query

    def __iter__(self):
        self._fetch_all()
        try:
            cache_ = self._my_cache.copy()
            pks = [pk for pk in self._pks_order]
        except AttributeError:
            yield from self._result_cache
        else:
            for pk in pks:
                while cache_[pk]:
                    yield cache_[pk].pop()

    def iterator(self, chunk_size=None):
        yield from self.__iter__()

    def annotate(self, *args, **kwargs):
        self._annotate_args.extend(args)
        self._annotate_kwargs.update(kwargs)
        return super().annotate(*args, **kwargs)

    def extra(self, *args, **kwargs):
        self._extra_args.extend(args)
        self._extra_kwargs.update(kwargs)
        return super().extra(*args, **kwargs)

    def _clone(self):
        clone = super()._clone()
        clone._polymorphic_select_related = self._polymorphic_select_related.copy()
        clone._polymorphic_prefetch_related = self._polymorphic_prefetch_related.copy()
        clone._annotate_kwargs = self._annotate_kwargs.copy()
        clone._annotate_args = self._annotate_args.copy()
        clone._extra_args = self._extra_args.copy()
        clone._extra_kwargs = self._extra_kwargs.copy()
        clone._polymorphic_filter_args = self._polymorphic_filter_args.copy()
        clone._polymorphic_filter_kwargs = self._polymorphic_filter_kwargs.copy()
        clone._my_cache = self._my_cache.clone() if self._my_cache else None
        clone._pks_order = self._pks_order.clone() if self._pks_order else None
        return clone

    def get(self, *args, **kwargs):
        obj = super().get(*args, **kwargs)
        if hasattr(obj, "content_type"):
            obj = obj.content_type.get_object_for_this_type(pk=obj.pk)
        return obj

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
        Extra filter for descendant model

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
        full_mro = set(tuple([mro for b in bases for mro in b.__mro__]) + bases)
        base_polymorphic = set([b for b in full_mro if issubclass(b, Polymorphic)])
        attrs["_polymorphic_descendants"] = []
        attrs["_polymorphic_models"] = base_polymorphic
        new_class = super().__new__(cls, name, bases, attrs)
        for polymorphic_class in base_polymorphic:
            # Set is_polymorphic flag for classes that use polymorphic
            polymorphic_class.is_polymorphic = True
            if new_class._meta.proxy:
                continue
            try:
                if (
                    new_class._meta.model_name == "vip"
                ):  # TODO remove after vip deletion
                    continue
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

    content_type = models.ForeignKey(
        ContentType, blank=True, null=True, on_delete=models.CASCADE
    )

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
