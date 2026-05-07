import asyncio
from app.db.base import Base
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.invoice import Invoice
from app.models.organization import Organization
from app.models.user import User
from app.models.role import Role
from app.models.vendor import Vendor
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.audit_log import AuditLog
from app.models.payment import Payment

async def init():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5434/ovm_db')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

if __name__ == "__main__":
    asyncio.run(init())
