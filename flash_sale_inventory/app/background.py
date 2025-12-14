import asyncio
import os
from app.crud import expire_reservation
from redis.asyncio import Redis


CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS"))
redis = Redis(host="redis", port=6379, decode_responses=True)


async def cleanup_task():
    """
    Periodically scan Redis keys reservation:* to find expired reservations.
    I used Redis key with TTL when creating reservation: reservation:{id} with ex=TTL.
    When that key expires, Redis just deletes it — I cannot reliably subscribe to expiry in all setups.
    So instead I store active reservations in a Redis SET "active_reservations" (members=res_id),
    and rely on TTL of individual keys to detect expiration: on each loop I scan the set and check ttl.
    If ttl == -2 (key missing) -> it's expired -> call expire_reservation.
    """
    while True:
        try:
            res_ids = await redis.smembers("active_reservations")

            for rid in list(res_ids):
                ttl = await redis.ttl(f"reservation:{rid}")

                if ttl == -2:
                    # reservation key missing => expired
                    success = expire_reservation(rid)

                    # remove from active_reservations set
                    await redis.srem("active_reservations", rid)

            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        except Exception as exc:
            print("cleanup task error", exc)
            
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
