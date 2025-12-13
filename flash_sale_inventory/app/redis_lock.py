import asyncio
import os
import uuid
from redis.asyncio import Redis


REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis = Redis(host="redis", port=6379, decode_responses=True)


class RedisLock:
    def __init__(self, key: str, ttl_ms: int=5000):
        self.key = key
        self.ttl_ms = ttl_ms
        self.token = str(uuid.uuid4())


    async def acquire(self, retry_delay=0.05, timeout=2.0):
        """
        Try to acquire the lock (SET NX PX)
        """
        import time


        start = time.time()
        
        while True:
            ok = await redis.set(self.key, self.token, nx=True, px=self.ttl_ms)

            if ok:
                return True
            
            if time.time() - start >= timeout:
                return False
            
            await asyncio.sleep(retry_delay)


    async def release(self):
        # release only if token matches (atomic via Lua)
        lua = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        
        try:
            await redis.eval(lua, keys=[self.key], args=[self.token])
        except Exception:
            pass
