import hashlib
import json
import logging
import os
import threading

from redis import Redis
from redis.exceptions import RedisError


_logger = logging.getLogger(__name__)
_lock = threading.Lock()
_redis_client = None
_redis_url = None
_VERSION_KEY = "trek-management:cache-version"
_KEY_PREFIX = "trek-management:cache"


def _get_redis_client():
    global _redis_client, _redis_url
    url = os.environ.get("REDIS_URL")
    if not url:
        return None

    with _lock:
        if url != _redis_url:
            _redis_client = Redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            _redis_url = url
        return _redis_client


def get_or_set(key, loader, timeout=60):
    client = _get_redis_client()
    if client is None:
        return loader()

    try:
        version = client.get(_VERSION_KEY) or "0"
        cache_key = f"{_KEY_PREFIX}:{version}:{hashlib.sha256(key.encode()).hexdigest()}"
        value = client.get(cache_key)
        if value is not None:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                _logger.warning("Ignoring invalid cached value for key %s", cache_key)
    except RedisError:
        _logger.warning("Redis cache read failed; loading data from the database", exc_info=True)
        return loader()

    result = loader()
    try:
        client.setex(cache_key, timeout, json.dumps(result, separators=(",", ":")))
    except RedisError:
        _logger.warning("Redis cache write failed; returning database result", exc_info=True)
    return result


def invalidate_cache():
    client = _get_redis_client()
    if client is None:
        return
    try:
        client.incr(_VERSION_KEY)
    except RedisError:
        _logger.warning("Redis cache invalidation failed", exc_info=True)
