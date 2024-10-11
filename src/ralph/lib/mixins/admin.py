from django.utils.safestring import mark_safe


class MemorizeBeforeStateMixin(object):
    """
    Mixin added _before_state to object which store object before save.
    """

    def save_model(self, request, obj, form, change):
        if change and obj.pk:
            obj._before_state = obj._meta.default_manager.get(pk=obj.pk)
        super().save_model(request, obj, form, change)


class ParentChangeMixin(MemorizeBeforeStateMixin):
    """
    Mixin display message when parent was changed. Works with admin when model
    has specified `_parent_attr` attribute.
    """
    add_message = ''
    change_message = ''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent_attr = self.model._parent_attr

    def get_add_message(self):
        return self.add_message

    def get_change_message(self):
        return self.change_message

    def response_add(self, request, obj, post_url_continue=None):
        parent = getattr(obj, self.parent_attr)
        if parent:
            message = None
            if obj:
                message = self.get_add_message().format(
                    parent.get_absolute_url(), parent
                )
                self.message_user(request, mark_safe(message))
        return super().response_add(request, obj, post_url_continue)

    def response_change(self, request, obj):
        parent = getattr(obj, self.parent_attr)
        message = None
        old_parent = getattr(obj._before_state, self.parent_attr)
        if parent and old_parent != parent:
            old_url = old_parent and old_parent.get_absolute_url() or ''
            parent_url = parent and parent.get_absolute_url() or ''
            message = self.get_change_message().format(
                old_url,
                old_parent,
                parent_url,
                parent
            )
        if message:
            self.message_user(request, mark_safe(message))
        return super().response_change(request, obj)
