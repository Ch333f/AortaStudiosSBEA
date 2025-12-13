from pydantic import BaseModel


class ReserveRequest(BaseModel):
    user_id: str
    sku: str


class PurchaseRequest(BaseModel):
    reservation_id: str
    user_id: str


class ReserveResponse(BaseModel):
    reservation_id: str
    product_id: int
    expires_at: int


class InventoryResponse(BaseModel):
    sku: str
    available_qty: int
