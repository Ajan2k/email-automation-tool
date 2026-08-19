from functools import lru_cache

import redis
from rq import Queue

from app.core.config import settings

EMAIL_QUEUE_NAME = "emails"


@lru_cache
def get_redis() -> redis.Redis:
    return redis.from_url(settings.redis_url)


@lru_cache
def get_email_queue() -> Queue:
    return Queue(EMAIL_QUEUE_NAME, connection=get_redis())
