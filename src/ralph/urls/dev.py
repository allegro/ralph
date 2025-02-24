import debug_toolbar
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.static import static

from ralph.urls import urlpatterns as base_urlpatterns
from ralph.urls import handler404  # noqa

urlpatterns = base_urlpatterns
urlpatterns += [
    url(r"^__debug__/", include(debug_toolbar.urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if "silk" in settings.INSTALLED_APPS:
    urlpatterns += [url(r"^silk/", include("silk.urls", namespace="silk"))]
