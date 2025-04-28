from django.contrib.auth.decorators import login_required
from django.urls import re_path

from ralph.accounts.views import (
    CurrentUserInfoView,
    InventoryTagConfirmationView,
    InventoryTagView,
    UserProfileView,
)

urlpatterns = [
    re_path(
        r"^user_profile/?$",
        login_required(UserProfileView.as_view()),
        name="user_profile",
    ),
    re_path(
        r"^my_equipment/?$",
        login_required(CurrentUserInfoView.as_view()),
        name="current_user_info",
    ),
    re_path(
        r"^my_equipment/inventory_tag/" r"(?P<asset_id>[0-9]+)/(?P<answer>yes|no)/$",
        login_required(InventoryTagConfirmationView.as_view()),
        name="inventory_tag_confirmation",
    ),
    re_path(
        r"^my_equipment/inventory_tag/$",
        login_required(InventoryTagView.as_view()),
        name="inventory_tag",
    ),
]
