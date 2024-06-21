from django.utils.deprecation import MiddlewareMixin
from threadlocals.middleware import \
    ThreadLocalMiddleware as ThreadLocalMiddleware_


class ThreadLocalMiddleware(ThreadLocalMiddleware_, MiddlewareMixin):
    pass
