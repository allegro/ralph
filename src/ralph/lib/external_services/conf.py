from django.conf import settings


def get_redis_connection_params():
    params = getattr(settings, 'REDIS_CONNECTION', {})
    return {k.lower(): v for k, v in params.items()}
