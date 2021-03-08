import logging
from collections import OrderedDict

from django.core.urlresolvers import NoReverseMatch
from django.utils.encoding import force_text
from rest_framework.metadata import SimpleMetadata
from rest_framework.relations import ManyRelatedField, RelatedField
from rest_framework.reverse import reverse

logger = logging.getLogger(__name__)


def get_list_view_name(model):
    """
    Return list view name for model.
    """
    return '{}-list'.format(
        model._meta.object_name.lower()
    )


def get_list_view_url_for_model(model):
    """
    Return url for API list resource for model.
    """
    view_name = get_list_view_name(model)
    return reverse(view_name)


class RalphApiMetadata(SimpleMetadata):
    """
    Add filtering variable to Django Rest Framework Meta.
    """
    def determine_metadata(self, request, view):
        data = super().determine_metadata(request, view)
        filtering = getattr(view, 'filter_fields', [])[:]
        filtering.extend(
            getattr(view, 'extended_filter_fields', {}).keys()
        )
        data['filtering'] = list(set(filtering))
        return data

    def get_field_info(self, field):
        """
        Given an instance of a serializer field, return a dictionary
        of metadata about it.

        Differences comparing to original `get_field_info`:
        * don't evaluate related field query (just provide url to this
          particular resource)
        """
        field_info = OrderedDict()
        field_info['type'] = self.label_lookup[field]
        field_info['required'] = getattr(field, 'required', False)

        attrs = [
            'read_only', 'label', 'help_text',
            'min_length', 'max_length',
            'min_value', 'max_value'
        ]

        for attr in attrs:
            value = getattr(field, attr, None)
            if value is not None and value != '':
                field_info[attr] = force_text(value, strings_only=True)

        if getattr(field, 'child', None):
            field_info['child'] = self.get_field_info(field.child)
        elif getattr(field, 'fields', None):
            field_info['children'] = self.get_serializer_info(field)

        # for RelatedField just return url to resource
        if isinstance(field, RelatedField):
            if field.queryset:
                model = field.queryset.model
                try:
                    field_info['url'] = get_list_view_url_for_model(
                        model
                    )
                except NoReverseMatch:
                    logger.warning('Reverse for %s not found', model)
        elif isinstance(field, ManyRelatedField):
            # for ManyRelatedField just return url to resource
            try:
                model = field.child_relation.queryset.model
            except AttributeError:
                pass
            else:
                try:
                    field_info['url'] = get_list_view_url_for_model(model)
                except NoReverseMatch:
                    logger.warning('Reverse for %s not found', model)
        # otherwise act as usual
        elif not field_info.get('read_only') and hasattr(field, 'choices'):
            field_info['choices'] = [
                {
                    'value': choice_value,
                    'display_name': force_text(choice_name, strings_only=True)
                }
                for choice_value, choice_name in field.choices.items()
            ]

        return field_info
