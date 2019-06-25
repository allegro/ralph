from django import http
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def page_not_found(request):
    body = (
        "<h1>Not Found</h1>"
        "<p>The requested resource was not found on this server.</p>"
    )
    content_type = 'text/html'
    return http.HttpResponseNotFound(body, content_type=content_type)
