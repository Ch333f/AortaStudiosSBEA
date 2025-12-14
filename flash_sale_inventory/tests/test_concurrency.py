import pytest
import os
from scripts.load_test import run as load_run
from sqlalchemy import create_engine, text


pytestmark = pytest.mark.asyncio  # <- this tells pytest all tests here can be async
DATABASE_URL = os.getenv("DATABASE_URL_LOCAL")


async def test_high_concurrency_inventory_safety():
    results = await load_run()

    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        qty = conn.execute(
            text("SELECT available_qty FROM products WHERE sku='BLACK-FRIDAY-ITEM'")
        ).scalar_one()

    # Assertions that matter
    assert results["exceptions"] == 0, "No unexpected exceptions under load"
    assert qty >= 0, "Inventory must never go negative"
    assert results["reserved"] <= 100, "Cannot reserve more than initial stock"

    print("Test summary:", results)
