from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from ralph.accounts.views import CurrentUserInfoView, UserProfileView

urlpatterns = [
    url(
        r'^user_profile/?$',
        UserProfileView.as_view(),
        name='user_profile'
    ),
    url(
        r'^my_equipment/?$',
        login_required(CurrentUserInfoView.as_view()),
        name='current_user_info'
    ),
]
