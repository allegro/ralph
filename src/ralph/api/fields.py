from collections import OrderedDict

from rest_framework.fields import (
    ChoiceField,
    Field,
    MultipleChoiceField,
    ReadOnlyField
)


class StrField(Field):
    def __init__(self, **kwargs):
        self._show_type = kwargs.pop("show_type", False)
        kwargs["read_only"] = True
        if "label" not in kwargs:
            kwargs["label"] = "__str__"
        super().__init__(**kwargs)

    def get_attribute(self, obj):
        # return obj to pass whole object to `to_representation`
        return obj

    def to_representation(self, obj):
        if self._show_type:
            return "{}: {}".format(obj._meta.verbose_name, str(obj))
        else:
            return str(obj)


class ReversedChoiceField(ChoiceField):
    """
    Choice field serializer which allow to pass value by name instead of key.
    Additionally it present value in user-friendly format by-name.

    Notice that requirement for this field to work properly is uniqueness of
    choice values.

    This field works perfectly with `dj.choices.Choices`.
    """

    def __init__(self, choices, **kwargs):
        super(ReversedChoiceField, self).__init__(choices, **kwargs)
        # mapping by value
        self.reversed_choices = OrderedDict([(v, k) for (k, v) in choices])

    def to_representation(self, obj):
        """
        Return choice name (value) instead of default key.
        """
        try:
            return self.choices[obj]
        except KeyError:
            return super().to_representation(obj)

    def to_internal_value(self, data):
        """
        Try to get choice by value first. If it doesn't succeed fallback to
        default action (get by key).
        """
        try:
            return self.reversed_choices[data]
        except KeyError:
            pass
        return super(ReversedChoiceField, self).to_internal_value(data)


class ModelMultipleChoiceField(MultipleChoiceField):
    """
    Multiple Model Choices Field for Django Rest Framework

    Changes list of integer data to Django Model queryset
    """

    def __init__(self, *args, **kwargs):
        self.model = kwargs["choices"].queryset.model
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if data:
            return self.model.objects.filter(pk__in=data)
        return self.model.objects.none()


class AbsoluteUrlField(ReadOnlyField):
    """
    A read-only field that returns full URL to object.
    """

    def get_attribute(self, obj):
        request = self.context.get("request", None)
        obj_url_func = getattr(obj, "get_absolute_url", None)
        value = ""
        if request and obj_url_func:
            value = request.build_absolute_uri(obj_url_func())
        return value
