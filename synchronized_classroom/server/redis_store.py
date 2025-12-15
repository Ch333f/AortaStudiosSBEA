import json
import redis
from typing import List


class RedisCommentStore:
    """
    Redis Sorted Set implementation for temporal comment indexing.
    """
    def __init__(self, redis_url: str):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)


    def add_comment(self, classroom_id: str, timestamp: float, payload: dict):
        key = f"classroom:{classroom_id}:comments"
        self.redis.zadd(key, {json.dumps(payload): timestamp})


    def get_comments_between(
        self, classroom_id: str, start: float, end: float
    ) -> List[dict]:
        key = f"classroom:{classroom_id}:comments"
        raw = self.redis.zrangebyscore(key, start, end)
        
        return [json.loads(item) for item in raw]
