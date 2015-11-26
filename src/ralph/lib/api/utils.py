from rest_framework.metadata import SimpleMetadata
from rest_framework.relations import RelatedField


class RalphApiMetadata(SimpleMetadata):
    """
    Add filtering variable to Django Rest Framework Meta.
    """
    def determine_metadata(self, request, view):
        data = super().determine_metadata(request, view)
        filtering = getattr(view, 'filter_fields', [])[:]
        filtering.extend(
            getattr(view, 'extend_filter_fields', {}).keys()
        )
        data['filtering'] = list(set(filtering))
        return data

    def get_field_info(self, field):
        """
        Delete choices for foreign keys
        """
        field_info = super().get_field_info(field)
        if 'choices' in field_info and isinstance(field, RelatedField):
            del field_info['choices']
            # TODO: add link to model resource
        return field_info
