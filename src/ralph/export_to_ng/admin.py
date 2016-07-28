from django.db.models.signals import post_save


class Ralph3SyncAdminMixin(object):
    """
    Mixin for Django Admin to properly handle syncing related objects (m2m).
    Sync is triggered after saving m2m, not before (like in regular admin).
    """
    def save_model(self, request, obj, form, change):
        # hold on syncing until m2m relations are saved
        obj._handle_post_save = False
        return super(Ralph3SyncAdminMixin, self).save_model(
            request, obj, form, change
        )

    def _sync_to_ralph2(self, obj, created=False):
        obj._handle_post_save = True
        post_save.send(
            sender=self.model,
            instance=obj,
            created=created,
            raw=None,
            using='default',
        )

    # log_addition and log_change are called after succesfull save (with m2m)
    def log_addition(self, request, obj):
        self._sync_to_ralph2(obj, True)
        return super(Ralph3SyncAdminMixin, self).log_addition(request, obj)

    def log_change(self, request, obj, change_message):
        self._sync_to_ralph2(obj, False)
        return super(Ralph3SyncAdminMixin, self).log_change(
            request, obj, change_message
        )
