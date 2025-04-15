from django.db.models import Q

from ralph.assets.models import Service
from ralph.lib.visibility_scope.models import ServiceBasedVisibilityScope


def visibility_scopes_for_user(user):
    return ServiceBasedVisibilityScope.objects.filter(
        Q(id__in=user.service_visibility_scopes.all()) | Q(group__in=user.groups.all())
    )


def visibility_scope_filter(user):
    if user.is_superuser:
        return Q()

    scopes = visibility_scopes_for_user(user)
    if not scopes:
        return Q()

    return Q(
        service_env__service__in=Service.objects.filter(visibility_scopes__in=scopes)
    )


def visibility_scope_asset_support_filter(user):
    """Only show BaseObjectsSupport for which assets belong to the service"""
    if user.is_superuser:
        return Q()

    scopes = visibility_scopes_for_user(user)
    if not scopes:
        return Q()

    return Q(
        baseobject__service_env__service__in=Service.objects.filter(
            visibility_scopes__in=scopes
        )
    )
