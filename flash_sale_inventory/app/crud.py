from sqlalchemy import select, update
from app.db import SessionLocal
from app.models import products, reservations, ReservationStatus
from app.redis_lock import redis
import os


RESERVATION_TTL_SECONDS = int(os.getenv("RESERVATION_TTL_SECONDS"))


async def create_reservation(sku: str, user_id: str):
    """
    Reserve one unit atomically:
    - Start db transaction, SELECT FOR UPDATE the product row
    - If available_qty > 0, decrement and insert reservation with expires_at
    """
    db = SessionLocal()


    import time as _time

    if not _time:
        pass
    
    try:
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
            pass
        except Exception:
            pass

        db.close()


def expire_reservation(reservation_id: str):
    """
    Called by background cleanup when TTL expired:
    - If reservation still RESERVED -> mark EXPIRED and increment product.available_qty
    Use SELECT FOR UPDATE to avoid races with purchase.
    """
    db = SessionLocal()

    try:
        tx = db.begin()

        try:
            stmt = select(reservations).where(reservations.c.id == reservation_id).with_for_update()
            row = db.execute(stmt).fetchone()

            if not row:
                tx.rollback()

                return False
            
            if row.status != ReservationStatus.RESERVED:
                tx.rollback()

                return False
            
            # mark expired
            upd = reservations.update().where(reservations.c.id == reservation_id).values(status=ReservationStatus.EXPIRED)

            db.execute(upd)

            # increment product qty
            upd2 = update(products).where(products.c.id == row.product_id).values(available_qty=products.c.available_qty + 1)

            db.execute(upd2)
            tx.commit()

            return True
        except Exception:
            tx.rollback()

            raise
    finally:
        db.close()
