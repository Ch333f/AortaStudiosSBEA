from fastapi import FastAPI
from app import models
from app.db import engine


models.metadata.create_all(bind=engine)

app = FastAPI(title="Flash Sale Inventory Service")
