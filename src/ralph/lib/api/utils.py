from rest_framework.metadata import SimpleMetadata


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
