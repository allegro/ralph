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

    def iterator(self):
        """
        Override iterator:
            - Iterate for all objects and collected ID
            - For each ContentType generates additional queryset
            - Returns iterator with different models
        """
        result = []
        content_type_model_map = {}
        for obj in super().iterator():
            content_type_model_map[
                obj.content_type_id
            ] = obj.content_type.model_class()
            result.append((
                obj.content_type_id, obj.pk)
            )
        result = groupby(result, lambda x: x[0])

        result_query = []
        for k, v in result:
            model = content_type_model_map[k]
            polymorphic_models = getattr(model, '_polymorphic_models', [])
            if polymorphic_models and model not in polymorphic_models:
                result_query.extend(
                    model.objects.filter(pk__in=[i[1] for i in v])
                )

        for obj in result_query:
            yield obj


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
