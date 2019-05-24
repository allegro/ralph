from django.conf import settings
from redis_cache import RedisCache

from ralph.lib.redis import get_redis_connection


class DjangoConnectionPoolCache(RedisCache):

    def __init__(self, server, params):
        """
        Connect to Redis using connection pool
        """
        # Internal attrs used to cache created clients
        self._client = None
        self._master_client = None

        # Set server params to empty
        # The passed params will be not used, but there is no easy way to
        # to extend connection configuration.
        super(DjangoConnectionPoolCache, self).__init__(server, params)

        self.master_client = self.get_master_client()

    def get_client(self, key, write=False):
        if write:
            return self.master_client

        if self._client:
            return self._client

        self._client = get_redis_connection(
            settings.REDIS_CONNECTION, is_master=False
        )
        return self._client

    def get_master_client(self):
        return get_redis_connection(settings.REDIS_CONNECTION, is_master=True)
