from fastapi import FastAPI
from app import models
from app.db import engine
from app.background import cleanup_task
import asyncio


models.metadata.create_all(bind=engine)

app = FastAPI(title="Flash Sale Inventory Service")


@app.on_event("startup")
async def start_background_tasks():
    app.state.cleanup = asyncio.create_task(cleanup_task())


@app.get("/")
def root():
    return {"status": "ok"}
