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
        <Model3: model3L test>
    ]
"""
from itertools import groupby

from django.contrib.contenttypes.models import ContentType
from django.db import models


class PolymorphicQuerySet(models.QuerySet):
    _polymorphic_select_related = {}
    _polymorphic_prefetch_related = {}

    def iterator(self):
        """
        Override iterator:
            - Iterate for all objects and collected ID
            - For each ContentType generates additional queryset
            - Returns iterator with different models
        """
        result = []
        content_types_ids = set()
        for obj in super().iterator():
            content_types_ids.add(obj.content_type_id)
            result.append((
                obj.content_type_id, obj.pk)
            )
        result = groupby(result, lambda x: x[0])

        content_type_model_map = {
            ct.id: ct.model_class() for ct in ContentType.objects.filter(
                pk__in=list(content_types_ids)
            )
        }

        # result_query = []
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
                if model_name in self._polymorphic_select_related:
                    model_query = model_query.select_related(
                        *self._polymorphic_select_related[model_name]
                    )
                if model_name in self._polymorphic_prefetch_related:
                    model_query = model_query.prefetch_related(
                        *self._polymorphic_prefetch_related[model_name]
                    )
                for obj in model_query:
                    yield obj

    def _clone(self, *args, **kwargs):
        clone = super()._clone(*args, **kwargs)
        clone._polymorphic_select_related = (
            self._polymorphic_select_related.copy()
        )
        clone._polymorphic_prefetch_related = (
            self._polymorphic_prefetch_related.copy()
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
