from threadlocals.middleware import ThreadLocalMiddleware as ThreadLocalMiddleware_
from django.utils.deprecation import MiddlewareMixin


class ThreadLocalMiddleware(ThreadLocalMiddleware_, MiddlewareMixin):
    pass
