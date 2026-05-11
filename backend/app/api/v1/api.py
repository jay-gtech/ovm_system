from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth, health, organizations, users, vendors, products,
    purchase_orders, invoices, payments, vendor_settlements, monitoring, audit,
    alerts, notifications, sla, risk_assessments, documents, ops, grn
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(ops.router, prefix="/ops", tags=["ops"])
api_router.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(vendors.router, prefix="/vendors", tags=["vendors"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["purchase-orders"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["invoices"])
api_router.include_router(grn.router, prefix="/grns", tags=["grns"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(vendor_settlements.router, prefix="/settlements", tags=["vendor-settlements"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["monitoring"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(sla.router, prefix="/sla/policies", tags=["sla"])
api_router.include_router(risk_assessments.router, prefix="/risk-assessments", tags=["risk-assessments"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
