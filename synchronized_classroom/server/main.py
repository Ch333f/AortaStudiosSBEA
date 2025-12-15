import uuid
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from server.redis_store import RedisCommentStore
from server.websocket_manager import ConnectionManager
from server.time_sync import server_time
from server.models import Comment
from server.redis_pubsub import RedisPubSub


app = FastAPI()
manager = ConnectionManager()
REDIS_URL = os.getenv("REDIS_URL")
store = RedisCommentStore(REDIS_URL)
CLASSROOM_ID = "default"


def on_pubsub_message(payload):
    import asyncio

    # Fan-out to local WebSocket clients
    asyncio.create_task(manager.broadcast(payload))


pubsub = RedisPubSub(
    REDIS_URL,
    channel="classroom-events",
    on_message=on_pubsub_message
)

pubsub.start()


@app.websocket("/ws/{user_id}")
async def classroom_ws(ws: WebSocket, user_id: str):
    await manager.connect(user_id, ws)

    # Initial server time sync
    await ws.send_json({
        "type": "sync",
        "server_time": server_time()
    })

    try:
        while True:
            data = await ws.receive_json()

            # Post comment
            if data["type"] == "comment":
                comment = Comment(
                    id=str(uuid.uuid4()),
                    video_timestamp=data["video_ts"],
                    message=data["message"],
                    author=data["author"],
                    created_at=server_time()
                )

                store.add_comment(
                    CLASSROOM_ID,
                    comment.video_timestamp,
                    comment.dict()
                )

                await manager.broadcast({
                    "type": "comment",
                    "user": user_id,
                    "payload": data,
                    "comment": comment.dict()
                })

            # Seek / Join history
            elif data["type"] == "seek":
                comments = store.get_comments_between(
                    CLASSROOM_ID,
                    0,
                    data["video_ts"]
                )

                await ws.send_json({
                    "type": "history",
                    "comments": comments
                })

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(user_id)
