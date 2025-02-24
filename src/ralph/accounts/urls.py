from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from ralph.accounts.views import (
    CurrentUserInfoView,
    InventoryTagConfirmationView,
    InventoryTagView,
    UserProfileView
)

urlpatterns = [
    url(
        r"^user_profile/?$",
        login_required(UserProfileView.as_view()),
        name="user_profile",
    ),
    url(
        r"^my_equipment/?$",
        login_required(CurrentUserInfoView.as_view()),
        name="current_user_info",
    ),
    url(
        r"^my_equipment/inventory_tag/" r"(?P<asset_id>[0-9]+)/(?P<answer>yes|no)/$",
        login_required(InventoryTagConfirmationView.as_view()),
        name="inventory_tag_confirmation",
    ),
    url(
        r"^my_equipment/inventory_tag/$",
        login_required(InventoryTagView.as_view()),
        name="inventory_tag",
    ),
]
