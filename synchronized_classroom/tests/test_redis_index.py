from server.redis_store import RedisCommentStore
import os
from dotenv import load_dotenv


load_dotenv()  # load variables from .env

redis_client = os.getenv("REDIS_URL")


def test_add_and_fetch():
    store = RedisCommentStore(redis_client)
    
    store.add_comment("test", 5.0, {"msg": "hello"})

    results = store.get_comments_between("test", 0, 10)

    assert len(results) == 1

    print("Test summary:", results)
