from django.contrib import admin

from ralph.lib.permissions.admin import PermissionAdminMixin
from ralph.lib.permissions.tests.models import Article


@admin.register(Article)
class ArticleAdmin(PermissionAdminMixin, admin.ModelAdmin):
    list_display = [
        'author', 'title', 'content', 'custom_field_1', 'sample_admin_field',
        'sample_admin_field_with_permissions', '_sample_property'
    ]

    def sample_admin_field(self, obj):
        return 'abc'

    def sample_admin_field_with_permissions(self, obj):
        return 'def'
    sample_admin_field_with_permissions._permission_field = 'custom_field_1'
