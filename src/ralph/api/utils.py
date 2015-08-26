from ralph.admin.sites import ralph_site


class QuerysetRelatedMixin(object):
    """
    Allow to specify select_related and prefetch_related for queryset.

    Default select_related is taken from related admin site
    `list_select_related` attribute.
    """
    select_related = None
    prefetch_related = None
    _skip_admin_list_select_related = False

    def __init__(self, *args, **kwargs):
        self.select_related = kwargs.pop('select_related', self.select_related)
        self.prefetch_related = kwargs.pop(
            'prefetch_related', self.prefetch_related
        )
        super().__init__(*args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        admin_site = ralph_site._registry.get(queryset.model)
        if self.select_related:
            queryset = queryset.select_related(*self.select_related)
        if self.prefetch_related:
            queryset = queryset.prefetch_related(*self.prefetch_related)
        if (
            admin_site and
            not self._skip_admin_list_select_related and
            admin_site.list_select_related
        ):
            queryset = queryset.select_related(*admin_site.list_select_related)
        return queryset
