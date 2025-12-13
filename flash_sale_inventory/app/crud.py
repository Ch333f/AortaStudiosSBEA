from sqlalchemy import select, update
from app.db import SessionLocal
from app.models import products, reservations, ReservationStatus
from app.redis_lock import RedisLock, redis
import os


RESERVATION_TTL_SECONDS = int(os.getenv("RESERVATION_TTL_SECONDS", "300"))


async def create_reservation(sku: str, user_id: str):
    """
    Reserve one unit atomically:
    - Acquire redis lock per sku
    - Start db transaction, SELECT FOR UPDATE the product row
    - If available_qty > 0, decrement and insert reservation with expires_at
    - Release redis lock
    """
    db = SessionLocal()
    lock = RedisLock(f"lock:sku:{sku}", ttl_ms=2000)


    import time as _time

    if not _time:
        pass
    
    try:
        # Acquire distributed lock to limit race across app instances
        ok = await lock.acquire(timeout=2.0)

        if not ok:
            raise Exception("could not acquire lock, try again")

        tx = db.begin()

        try:
            # lock row
            stmt = select(products).where(products.c.sku == sku).with_for_update()
            row = db.execute(stmt).fetchone()

            if not row:
                tx.rollback()

                return {"error": "sku_not_found"}
            
            if row.available_qty <= 0:
                tx.rollback()

                return {"error": "out_of_stock"}

            # decrement
            new_q = row.available_qty - 1
            upd = update(products).where(products.c.id == row.id).values(available_qty=new_q)

            db.execute(upd)

            now_ms = int(_time.time() * 1000)
            expires_at = now_ms + RESERVATION_TTL_SECONDS * 1000
            res_id = __import__("uuid").uuid4()
            ins = reservations.insert().values(
                id=str(res_id),
                product_id=row.id,
                user_id=user_id,
                status=ReservationStatus.RESERVED,
                expires_at=expires_at,
                created_at=now_ms,
            )
            
            db.execute(ins)
            tx.commit()

            # store mapping in Redis to allow faster expiry/cleanup
            # Key: reservation:{reservation_id} -> product_id , expire ttl

            await redis.set(
                f"reservation:{res_id}",
                f"{row.id}",
                ex=RESERVATION_TTL_SECONDS
            )

            return {"reservation_id": str(res_id), "product_id": row.id, "expires_at": expires_at}
        except Exception as e:
            tx.rollback()

            raise
        finally:
            pass
    finally:
        try:
            await lock.release()
        except Exception:
            pass
        
        db.close()
