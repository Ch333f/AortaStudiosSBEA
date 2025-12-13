from sqlalchemy import Table, Column, Integer, String, MetaData, DateTime, ForeignKey, Enum, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import enum
import uuid


metadata = MetaData()


class ReservationStatus(str, enum.Enum):
    RESERVED = "reserved"
    PURCHASED = "purchased"
    EXPIRED = "expired"


products = Table(
    "products",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("sku", String, unique=True, nullable=False),
    Column("available_qty", Integer, nullable=False, default=0),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)
reservations = Table(
    "reservations",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("product_id", Integer, ForeignKey("products.id"), nullable=False, index=True),
    Column("user_id", String, nullable=False),  # simplified user identifier
    Column("status", Enum(ReservationStatus), nullable=False, default=ReservationStatus.RESERVED),
    Column("expires_at", BigInteger, nullable=False),  # epoch ms expiration
    Column("created_at", BigInteger, nullable=False),  # epoch ms created
)
