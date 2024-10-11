# -*- coding: utf-8 -*-
import logging

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.auth.views import redirect_to_login
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseForbidden

from ralph.admin.sites import ralph_site

logger = logging.getLogger(__name__)

_permission_views = []


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
        for model in [kwargs.get('model'), user_model]:
            if not model:
                continue
            perm_name = '{}.{}'.format(
                model._meta.app_label, self.permision_codename
            )
            if request.user.has_perm(perm_name):
                return func(self, request, *args, **kwargs)
        logger.info('{} permission not set for user {}'.format(
            self.permision_codename, request.user
        ))
        return HttpResponseForbidden()
    return wraps


class PermissionViewMetaClass(type):

    """
    Adding permission to additional views.
    """

    def __new__(cls, name, bases, attrs):
        codename = 'can_view_extra_{}'.format(name.lower())

        attrs['permision_codename'] = codename
        new_class = super().__new__(cls, name, bases, attrs)
        dispatch = getattr(new_class, 'dispatch', None)
        setattr(new_class, 'dispatch', view_permission_dispatch(dispatch))
        _permission_views.append((new_class, codename))
        return new_class


def update_extra_view_permissions(sender, **kwargs):
    """
    Get all views that inherit the PermissionViewMetaClass and
    adding them permission.
    """
    if sender.name != 'django.contrib.auth':
        return
    logger.info('Updating extra views permissions...')
    admin_classes = {}
    for model, admin_class in ralph_site._registry.items():
        if admin_class.change_views:
            for change_view in admin_class.change_views:
                admin_classes[change_view] = model

    old_permission = Permission.objects.filter(
        codename__startswith='can_view_extra_'
    ).values_list('id', flat=True)
    current_permission = []
    for class_view, codename in _permission_views:
        model = admin_classes.get(class_view, None)
        if not model:
            model = get_user_model()
        ct = ContentType.objects.get_for_model(model)
        perm, _ = Permission.objects.get_or_create(
            content_type=ct,
            codename=codename,
            defaults={'name': 'Can view {}'.format(class_view.__name__)}
        )
        current_permission.append(perm.id)

    # Remove old permission codename views.
    permission_ids = set(old_permission) - set(current_permission)
    if permission_ids:
        logger.warning(
            'Removing unused permissions: %s',
            ", ".join(
                Permission.objects.filter(id__in=permission_ids).values_list(
                    'codename', flat=True
                )
            )
        )
        Permission.objects.filter(id__in=permission_ids).delete()
