import redis
import threading
import json


class RedisPubSub:
    def __init__(self, redis_url: str, channel: str, on_message):
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.channel = channel
        self.on_message = on_message


    def start(self):
        thread = threading.Thread(target=self._listen, daemon=True)
        thread.start()


    def _listen(self):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(self.channel)

        for msg in pubsub.listen():
            if msg["type"] == "message":
                payload = json.loads(msg["data"])
                self.on_message(payload)


    def publish(self, payload: dict):
        self.redis.publish(self.channel, json.dumps(payload))
