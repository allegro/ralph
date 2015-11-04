from rest_framework.metadata import SimpleMetadata


class RalphApiMetadata(SimpleMetadata):
    """
    Add filtering variable to Django Rest Framework Meta.
    """
    def determine_metadata(self, request, view):
        data = super().determine_metadata(request, view)
        data['filtering'] = set(getattr(view, 'filter_fields', []))
        return data
