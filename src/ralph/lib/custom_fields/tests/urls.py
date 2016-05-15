from django.conf.urls import include, url

from . import admin

urlpatterns = [
    url(r'^cf_admin/', include(admin.site.urls)),
]
