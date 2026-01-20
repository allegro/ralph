"""
Utility functions for extra view permissions management.
"""

from dataclasses import dataclass
from typing import Optional

from django.contrib.auth.models import Group, Permission

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
    error: Optional[str] = None


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


def query_permissions():
    """Returns all extra view permissions."""
    return Permission.objects.filter(
        codename__startswith=EXTRA_VIEW_PERMISSION_PREFIX
    ).select_related("content_type")


def query_orphaned_permissions():
    """Returns permissions not associated with any registered view."""
    return query_permissions().exclude(codename__in=get_registered_codenames())


def get_permission_groups(perm: Permission) -> list[str]:
    """Returns group names that have the given permission."""
    return list(perm.group_set.values_list("name", flat=True))


def collect_permission_info(
    include_groups: bool = False,
    orphaned_only: bool = False,
) -> tuple[list[PermissionInfo], int, int]:
    """
    Collects permission data for all extra view permissions.

    Returns: (permissions, active_count, orphaned_count)
    """
    orphaned_codenames = set(
        query_orphaned_permissions().values_list("codename", flat=True)
    )

    result = []
    for perm in query_permissions():
        is_orphaned = perm.codename in orphaned_codenames

        if orphaned_only and not is_orphaned:
            continue

        result.append(
            PermissionInfo(
                codename=perm.codename,
                name=perm.name,
                content_type=str(perm.content_type),
                is_orphaned=is_orphaned,
                groups=get_permission_groups(perm) if include_groups else [],
            )
        )

    return result, len(get_registered_codenames()), len(orphaned_codenames)


def export_permission_mappings() -> dict[str, list[str]]:
    """Exports current permission-group mappings as {codename: [group_names]}."""
    return {
        perm.codename: get_permission_groups(perm)
        for perm in query_permissions().prefetch_related("group_set")
        if perm.group_set.exists()
    }


def assign_permission_to_group(codename: str, group_name: str) -> AssignmentResult:
    """Assigns a permission to a group."""
    try:
        perm = Permission.objects.get(codename=codename)
    except Permission.DoesNotExist:
        return AssignmentResult(False, f"Permission '{codename}' does not exist")

    try:
        group = Group.objects.get(name=group_name.strip())
    except Group.DoesNotExist:
        return AssignmentResult(False, f"Group '{group_name}' does not exist")

    group.permissions.add(perm)
    return AssignmentResult(True)
