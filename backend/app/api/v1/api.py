from fastapi import APIRouter
from app.api.v1.endpoints import auth, health, organizations, users, vendors, products, purchase_orders, invoices, payments, vendor_settlements, monitoring

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase-orders"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(vendor_settlements.router, prefix="/settlements", tags=["vendor-settlements"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
