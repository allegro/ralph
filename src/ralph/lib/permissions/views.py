import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden

from ralph.admin.sites import ralph_site

logger = logging.getLogger(__name__)

_permission_views = []

EXTRA_VIEW_PERMISSION_PREFIX = "can_view_extra_"


def view_permission_dispatch(func):
    """
    Adding to check the user has permission to dispatch method.
    """

    def wraps(self, request, *args, **kwargs):
        # If not logged in redirect to login page instead of returning 403
        # status code.
        if not request.user.is_authenticated:
            return redirect_to_login(next=request.get_full_path())
        # first try by model passed in kwargs, then, if user has not this perm
        # try by checking if this perm is assigned directly to user
        # (this happen ex. in transitions - user has perm to run transition at
        # all, but concrete model has perm to run particular transition)
        user_model = get_user_model()
        for model in [kwargs.get("model"), user_model]:
            if not model:
                continue
            perm_name = "{}.{}".format(model._meta.app_label, self.permision_codename)
            if request.user.has_perm(perm_name):
                return func(self, request, *args, **kwargs)
        logger.info(
            "{} permission not set for user {}".format(self.permision_codename, request.user)
        )
        return HttpResponseForbidden()

    return wraps


class PermissionViewMetaClass(type):
    """
    Adding permission to additional views.
    """

    def __new__(cls, name, bases, attrs):
        codename = "{}{}".format(EXTRA_VIEW_PERMISSION_PREFIX, name.lower())

        attrs["permision_codename"] = codename
        new_class = super().__new__(cls, name, bases, attrs)
        dispatch = getattr(new_class, "dispatch", None)
        new_class.dispatch = view_permission_dispatch(dispatch)
        _permission_views.append((new_class, codename))
        return new_class


def _get_admin_view_mapping():
    """Returns a mapping of view classes to their associated models."""
    admin_classes = {}
    for model, admin_class in ralph_site._registry.items():
        if admin_class.change_views:
            for change_view in admin_class.change_views:
                admin_classes[change_view] = model
    return admin_classes


def _get_registered_codenames():
    """Returns the set of codenames for all currently registered permission views."""
    return {codename for _, codename in _permission_views}


def get_orphaned_extra_view_permissions():
    """
    Returns a queryset of permissions that start with 'can_view_extra_' but
    are not associated with any currently registered view.

    Useful for identifying permissions that may need manual cleanup.
    """
    current_codenames = _get_registered_codenames()
    return Permission.objects.filter(codename__startswith=EXTRA_VIEW_PERMISSION_PREFIX).exclude(
        codename__in=current_codenames
    )


def update_extra_view_permissions(sender, **kwargs):
    """
    Get all views that inherit the PermissionViewMetaClass and
    adding them permission.

    NOTE: This function does NOT delete orphaned permissions to prevent
    accidental data loss when views are conditionally loaded (e.g., DNSView
    when ENABLE_DNSAAS_INTEGRATION is disabled). Use the management command
    `cleanup_extra_view_permissions` to manually remove unused permissions.
    """
    if sender.name != "django.contrib.auth":
        return
    logger.info("Updating extra views permissions...")

    admin_classes = _get_admin_view_mapping()

    old_permission_ids = set(
        Permission.objects.filter(codename__startswith=EXTRA_VIEW_PERMISSION_PREFIX).values_list(
            "id", flat=True
        )
    )

    current_permission_ids = []
    created_count = 0
    existing_count = 0

    for class_view, codename in _permission_views:
        model = admin_classes.get(class_view, None)
        if not model:
            model = get_user_model()
        ct = ContentType.objects.get_for_model(model)
        perm, created = Permission.objects.get_or_create(
            content_type=ct,
            codename=codename,
            defaults={"name": "Can view {}".format(class_view.__name__)},
        )
        current_permission_ids.append(perm.id)
        if created:
            created_count += 1
            logger.debug("Created permission: %s for model %s", codename, model)
        else:
            existing_count += 1

    logger.info(
        "Extra view permissions: %d total (%d created, %d existing)",
        len(current_permission_ids),
        created_count,
        existing_count,
    )

    # Identify orphaned permissions (not deleting them)
    orphaned_permission_ids = old_permission_ids - set(current_permission_ids)
    if orphaned_permission_ids:
        orphaned_codenames = Permission.objects.filter(id__in=orphaned_permission_ids).values_list(
            "codename", flat=True
        )
        logger.warning(
            "Found %d orphaned permission(s): %s. "
            "Run 'cleanup_extra_view_permissions' to remove them.",
            len(orphaned_permission_ids),
            ", ".join(orphaned_codenames),
        )
