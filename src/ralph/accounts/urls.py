from django.conf.urls import url

from ralph.accounts.views import UserProfileView

urlpatterns = [
    url(
        r'^user_profile/?$',
        UserProfileView.as_view(),
        name='user_profile'
    ),
]
