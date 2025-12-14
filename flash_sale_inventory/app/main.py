from fastapi import FastAPI, HTTPException
from app import models
from app.db import engine
from app.crud import create_reservation
from app.background import cleanup_task
import asyncio
import os
from redis.asyncio import Redis
from app.schemas import ReserveRequest


models.metadata.create_all(bind=engine)

app = FastAPI(title="Flash Sale Inventory Service")
redis = Redis(host="redis", port=6379, decode_responses=True)
RESERVATION_TTL_SECONDS = int(os.getenv("RESERVATION_TTL_SECONDS"))


@app.on_event("startup")
async def start_background_tasks():
    app.state.cleanup = asyncio.create_task(cleanup_task())


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/reserve")
async def reserve(req: ReserveRequest):
    """
    Try to reserve one unit for user_id on SKU.
    Returns reservation_id and expires_at (epoch ms) or error.
    """
    result = await create_reservation(req.sku, req.user_id)

    if result.get("error"):
        raise HTTPException(status_code=400, detail=result["error"])
            
    # store in active_reservations for cleanup detection
    res_id = result["reservation_id"]

    await redis.sadd("active_reservations", res_id)

    # ensure a key with TTL exists
    await redis.set(f"reservation:{res_id}", f"{result['product_id']}", ex=RESERVATION_TTL_SECONDS)

    return result
