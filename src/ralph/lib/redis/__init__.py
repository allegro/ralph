from django.conf import settings
from redis import StrictRedis
from redis.sentinel import Sentinel


def get_redis_connection(config, is_master=True):
    """
    Returns redis connection basing on configuration dict
    Args:
        config: Dict with configuration, if key `SENTINELS` is present
                sentinel connection pool will be used.
        is_master: Whether connection should be master or slave,
                   applies only if sentinels are used

    Returns: StrictRedis connection

    """
    if 'SENTINELS' in config:
        sentinel = Sentinel(
            config['SENTINELS'],
            db=config.get('DB'),
            password=config.get('PASSWORD'),
            socket_timeout=config.get('TIMEOUT'),
            socket_connect_timeout=config.get('CONNECT_TIMEOUT'),
        )
        if is_master:
            return sentinel.master_for(settings.REDIS_CLUSTER_NAME)
        else:
            return sentinel.slave_for(settings.REDIS_CLUSTER_NAME)
    else:
        return StrictRedis(
            host=config['HOST'],
            port=config['PORT'],
            db=config.get('DB'),
            password=config.get('PASSWORD'),
            socket_timeout=config.get('TIMEOUT'),
            socket_connect_timeout=config.get('CONNECT_TIMEOUT'),
        )
