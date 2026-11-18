"""
Utility functions for extra view permissions management.
"""

from collections import defaultdict
from dataclasses import dataclass

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.db.models import QuerySet

from ralph.admin.sites import ralph_site

EXTRA_VIEW_PERMISSION_PREFIX = "can_view_extra_"


@dataclass
class PermissionInfo:
    """Permission with metadata."""

    codename: str
    name: str
    content_type: str
    is_orphaned: bool
    groups: list[str] = None
    # number of groups with the permission
    group_count: int = 0
    # number of users with the permission assigned directly
    direct_user_count: int = 0
    # number of distinct users with the permission (directly or through groups)
    user_count: int = 0

    def __post_init__(self):
        if self.groups is None:
            self.groups = []

    @property
    def status(self) -> str:
        return "ORPHANED" if self.is_orphaned else "ACTIVE"


@dataclass
class AssignmentResult:
    """Result of a permission assignment operation."""

    success: bool
    error: str | None = None


def get_registered_codenames() -> set[str]:
    """Returns codenames for all currently registered permission views."""
    from ralph.lib.permissions.views import _permission_views

    return {codename for _, codename in _permission_views}


def get_admin_view_mapping() -> dict:
    """Returns a mapping of view classes to their associated models."""
    return {
        change_view: model
        for model, admin_class in ralph_site._registry.items()
        if admin_class.change_views
        for change_view in admin_class.change_views
    }


def query_permissions() -> QuerySet[Permission]:
    """Returns all extra view permissions."""
    return Permission.objects.filter(
        codename__startswith=EXTRA_VIEW_PERMISSION_PREFIX
    ).select_related("content_type")


def query_orphaned_permissions() -> QuerySet[Permission]:
    """Returns permissions not associated with any registered view."""
    return query_permissions().exclude(codename__in=get_registered_codenames())


def get_permission_groups(perm: Permission) -> list[str]:
    """Returns group names that have the given permission."""
    return list(perm.group_set.values_list("name", flat=True))


def _get_m2m_assignments(descriptor, target_ids) -> dict[int, set[int]]:
    """
    Returns mapping: target pk -> set of source pks for given many-to-many
    relation (ex. `Group.permissions`: permission pk -> group pks).
    """
    field = descriptor.field
    source = field.m2m_field_name()
    target = field.m2m_reverse_field_name()
    rows = field.remote_field.through.objects.filter(**{f"{target}__in": target_ids}).values_list(
        target, source
    )
    result = defaultdict(set)
    for target_id, source_id in rows:
        result[target_id].add(source_id)
    return result


def get_permission_assignment_counts(
    permissions: list[Permission],
) -> dict[int, tuple[int, int, int]]:
    """
    Counts groups and users to which given permissions are assigned.

    Superusers and inactive users are counted as any other user - only
    assignments are taken into account.

    Returns: mapping permission pk -> (group_count, direct_user_count, user_count),
    where `user_count` includes users with the permission assigned through groups.
    """
    user_model = get_user_model()
    permission_ids = [perm.pk for perm in permissions]

    groups_by_permission = _get_m2m_assignments(Group.permissions, permission_ids)
    direct_users_by_permission = _get_m2m_assignments(user_model.user_permissions, permission_ids)
    group_ids = set().union(*groups_by_permission.values())
    users_by_group = _get_m2m_assignments(user_model.groups, group_ids)

    result = {}
    for permission_id in permission_ids:
        permission_group_ids = groups_by_permission[permission_id]
        direct_users = direct_users_by_permission[permission_id]
        all_users = set(direct_users).union(
            *(users_by_group[group_id] for group_id in permission_group_ids)
        )
        result[permission_id] = (len(permission_group_ids), len(direct_users), len(all_users))
    return result


def collect_permission_info(
    include_groups: bool = False,
    orphaned_only: bool = False,
) -> tuple[list[PermissionInfo], int, int]:
    """
    Collects permission data for all extra view permissions.

    Returns: (permissions, active_count, orphaned_count)
    """
    orphaned_codenames = set(query_orphaned_permissions().values_list("codename", flat=True))

    permissions = list(query_permissions())
    counts = get_permission_assignment_counts(permissions)

    result = []
    for perm in permissions:
        is_orphaned = perm.codename in orphaned_codenames

        if orphaned_only and not is_orphaned:
            continue

        group_count, direct_user_count, user_count = counts[perm.pk]
        result.append(
            PermissionInfo(
                codename=perm.codename,
                name=perm.name,
                content_type=str(perm.content_type),
                is_orphaned=is_orphaned,
                groups=get_permission_groups(perm) if include_groups else [],
                group_count=group_count,
                direct_user_count=direct_user_count,
                user_count=user_count,
            )
        )

    return result, len(get_registered_codenames()), len(orphaned_codenames)
