class MemorizeBeforeStateMixin(object):

    def save_model(self, request, obj, form, change):
        """
        Given a model instance save it to the database.
        """
        if change and obj.pk:
            obj._before_state = obj._default_manager.get(pk=obj.pk)
        super().save_model(request, obj, form, change)
