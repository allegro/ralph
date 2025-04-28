import debug_toolbar
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.urls import re_path

from ralph.urls import urlpatterns as base_urlpatterns
from ralph.urls import handler404  # noqa

urlpatterns = base_urlpatterns
urlpatterns += [
    re_path(r"^__debug__/", include(debug_toolbar.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if "silk" in settings.INSTALLED_APPS:
    urlpatterns += [re_path(r"^silk/", include("silk.urls", namespace="silk"))]
