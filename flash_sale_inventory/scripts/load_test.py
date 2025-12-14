# Simulate N concurrent users trying to reserve the last item.
import asyncio
import httpx
import time
import uuid
from dotenv import load_dotenv
import os


load_dotenv()  # load variables from .env

API = os.getenv("API_URL")
CONCURRENCY = int(os.getenv("CONCURRENCY"))
SEM = asyncio.Semaphore(200)  # tune this


async def worker(i, sku, client):
    async with SEM:
        user_id = f"user-{i}-{uuid.uuid4().hex[:6]}"

        try:
            resp = await client.post(f"{API}/reserve", json={"user_id": user_id, "sku": sku}, timeout=10.0)

            if resp.status_code == 200:
                data = resp.json()
                
                print(f"[{i}] reserved -> {data['reservation_id']}")

                # optionally simulate purchase:
                # attempt to purchase immediately
                # await client.post(f"{API}/purchase", json={"reservation_id": data['reservation_id'], "user_id": user_id})
            else:
                print(f"[{i}] failed -> {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[{i}] exception {type(e).__name__}: {e}")


async def run():
    sku = "BLACK-FRIDAY-ITEM"

    async with httpx.AsyncClient() as client:
        tasks = []

        for i in range(CONCURRENCY):
            tasks.append(asyncio.create_task(worker(i, sku, client)))

        await asyncio.gather(*tasks)


if __name__ == "__main__":
    start = time.time()

    asyncio.run(run())
    
    print("done in", time.time() - start)
