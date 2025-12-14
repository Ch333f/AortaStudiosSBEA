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
results = {
    "reserved": 0,
    "r_failed": 0,
    "purchased": 0,
    "p_failed": 0,
    "exceptions": 0,
}


async def worker(i, sku, client):
    async with SEM:
        user_id = f"user-{i}-{uuid.uuid4().hex[:6]}"

        try:
            resp = await client.post(f"{API}/reserve", json={"user_id": user_id, "sku": sku}, timeout=10.0)

            if resp.status_code == 200:
                data = resp.json()
                
                print(f'[{i}] reserved -> {{"user_id": {user_id}, reservation_id": {data["reservation_id"]}}}')

                # optionally simulate purchase:
                # attempt to purchase immediately
                if os.getenv("PURCHASE_IMMEDIATELY"):
                    p_resp = await client.post(f"{API}/purchase", json={"reservation_id": data['reservation_id'], "user_id": user_id})

                    if p_resp.status_code == 200:
                        p_data = p_resp.json()

                        print(f'[{i}] purchased -> {p_data["message"]}')

                        results["purchased"] += 1
                    else:
                        print(f'[{i}] purchase failed -> {p_resp.status_code} {p_resp.text}')

                        results["p_failed"] += 1

                results["reserved"] += 1
            else:
                print(f"[{i}] failed -> {resp.status_code} {resp.text}")

                results["r_failed"] += 1
        except Exception as e:
            print(f"[{i}] exception {type(e).__name__}: {e}")

            results["exceptions"] += 1


async def run():
    sku = "BLACK-FRIDAY-ITEM"

    async with httpx.AsyncClient() as client:
        tasks = []

        for i in range(CONCURRENCY):
            tasks.append(asyncio.create_task(worker(i, sku, client)))

        await asyncio.gather(*tasks)

        return results


if __name__ == "__main__":
    start = time.time()

    asyncio.run(run())
    
    print("done in", time.time() - start)
