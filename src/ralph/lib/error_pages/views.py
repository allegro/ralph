from django import http
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import requires_csrf_token


@requires_csrf_token
def page_not_found(request, *args, **kwargs):
    header = _('Not Found')
    paragraph = _('The requested resource was not found on this server.')
    body = "<h1>{}</h1><p>{}</p>".format(header, paragraph)
    content_type = 'text/html'
    return http.HttpResponseNotFound(body, content_type=content_type)
