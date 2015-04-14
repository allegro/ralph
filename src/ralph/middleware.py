from threading import current_thread

from django.conf import settings
from django.contrib.auth.models import User

from ralph.account.models import Region


_requests = {}


def get_actual_regions():
    thread_name = current_thread().name
    if thread_name not in _requests:
        return Region.objects.filter(
            name=settings.DEFAULT_REGION_NAME,
        )
    return _requests[thread_name]['regions']


class RegionMiddleware(object):
    def process_request(self, request):
        if hasattr(request, 'user'):
            if request.user.is_anonymous():
                try:
                    user = User.objects.get(
                        username=request.GET.get('username'),
                        api_key__key=request.GET.get('api_key')
                    )
                except User.DoesNotExist:
                    user = None
            else:
                user = request.user
            if user:
                data = {
                    'user_id': user.id,
                    'regions': user.profile.get_regions(),
                }
                _requests[current_thread().name] = data

    def process_response(self, request, response):
        if hasattr(request, 'user') and not request.user.is_anonymous():
            _requests.pop(current_thread().name, None)
        return response
