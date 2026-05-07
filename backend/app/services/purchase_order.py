import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List
from app.models.purchase_order import PurchaseOrder, POLineItem, PurchaseOrderStatus
from app.models.vendor import VendorStatus
from app.models.product import ProductStatus
from app.schemas.purchase_order import PurchaseOrderCreate, PurchaseOrderStatusUpdate
from app.services.base import BaseService
from app.services.exceptions import (
    ResourceNotFoundException,
    BusinessRuleViolationException,
    UnauthorizedException
)
from app.core.context import get_tenant_id

_FOUR_DP = Decimal("0.0001")

# Allowlist of valid PO status transitions.
# Any transition not listed here is rejected.
_VALID_TRANSITIONS: dict[PurchaseOrderStatus, set[PurchaseOrderStatus]] = {
    PurchaseOrderStatus.DRAFT: {PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.APPROVED: {PurchaseOrderStatus.SENT, PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.SENT: {PurchaseOrderStatus.CANCELLED},
    PurchaseOrderStatus.CANCELLED: set(),
}


class PurchaseOrderService(BaseService):
    """
    Service layer for Purchase Order management.
    Handles orchestration, financial rules, and tenant validation.
    """

    async def create_purchase_order(
        self,
        data: PurchaseOrderCreate
    ) -> PurchaseOrder:
        """
        Create a new Purchase Order with line items.

        Financial Rules:
        - po_number must be unique per tenant.
        - vendor_id must belong to the tenant and be ACTIVE.
        - product_ids must belong to the tenant and be ACTIVE.
        - Snapshots generated from DB data at creation time.
        - All totals calculated server-side; client values ignored.
        """
        organization_id = get_tenant_id()
        if not organization_id:
            raise UnauthorizedException("Organization context missing")

        async with self.uow as uow:
            # 1. Validate PO number uniqueness within tenant
            existing_po = await uow.purchase_orders.get_by_po_number(
                uow.session, organization_id, data.po_number
            )
            if existing_po:
                raise BusinessRuleViolationException(
                    f"PO number {data.po_number} already exists"
                )

            # 2. Validate vendor — tenant-scoped get() + defence-in-depth org check
            vendor = await uow.vendors.get(uow.session, data.vendor_id)
            if not vendor or vendor.organization_id != organization_id:
                raise ResourceNotFoundException("Vendor", data.vendor_id)
            if vendor.is_deleted or vendor.status != VendorStatus.ACTIVE:
                raise BusinessRuleViolationException(
                    "Cannot create PO for an inactive or deleted vendor"
                )

            # 3. Process line items — validate, snapshot, and calculate server-side
            subtotal = Decimal("0.0000")
            line_item_models = []

            for item_data in data.line_items:
                product = await uow.products.get(uow.session, item_data.product_id)
                if not product or product.organization_id != organization_id:
                    raise ResourceNotFoundException("Product", item_data.product_id)
                if product.is_deleted:
                    raise BusinessRuleViolationException(
                        f"Product {product.sku} is deleted"
                    )
                if product.status != ProductStatus.ACTIVE:
                    raise BusinessRuleViolationException(
                        f"Product {product.sku} is not active"
                    )

                # Quantize to 4dp with ROUND_HALF_UP to match DB precision exactly
                line_total = (product.unit_price * item_data.quantity).quantize(
                    _FOUR_DP, rounding=ROUND_HALF_UP
                )
                subtotal += line_total

                line_item = POLineItem(
                    organization_id=organization_id,
                    product_id=product.id,
                    product_sku_snapshot=product.sku,
                    product_name_snapshot=product.name,
                    unit_price_snapshot=product.unit_price,
                    quantity=item_data.quantity,
                    line_total=line_total
                )
                line_item_models.append(line_item)

            # 4. Create PO header — totals are server-computed only
            po = PurchaseOrder(
                organization_id=organization_id,
                po_number=data.po_number,
                vendor_id=data.vendor_id,
                status=PurchaseOrderStatus.DRAFT,
                subtotal_amount=subtotal,
                total_amount=subtotal,  # No tax/shipping in foundation
                notes=data.notes,
                line_items=line_item_models
            )

            uow.session.add(po)
            await uow.commit()
            # Re-fetch after commit: session.refresh() does not reload relationships
            # in async SQLAlchemy; get_with_items() uses selectinload explicitly.
            return await uow.purchase_orders.get_with_items(
                uow.session, organization_id, po.id
            )

    async def get_purchase_order(self, id: uuid.UUID) -> PurchaseOrder:
        """Retrieve a PO by ID with tenant validation and eager line-item loading."""
        organization_id = get_tenant_id()
        async with self.uow as uow:
            po = await uow.purchase_orders.get_with_items(uow.session, organization_id, id)
            if not po:
                raise ResourceNotFoundException("PurchaseOrder", id)
            return po

    async def list_purchase_orders(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[PurchaseOrder]:
        """List POs for the current tenant. Tenant scope applied by BaseRepository."""
        async with self.uow as uow:
            return await uow.purchase_orders.get_multi(uow.session, skip=skip, limit=limit)

    async def update_po_status(
        self,
        id: uuid.UUID,
        status_update: PurchaseOrderStatusUpdate
    ) -> PurchaseOrder:
        """Update PO status enforcing the allowlist state machine."""
        organization_id = get_tenant_id()
        async with self.uow as uow:
            po = await uow.purchase_orders.get_with_items(uow.session, organization_id, id)
            if not po:
                raise ResourceNotFoundException("PurchaseOrder", id)

            allowed = _VALID_TRANSITIONS.get(po.status, set())
            if status_update.status not in allowed:
                raise BusinessRuleViolationException(
                    f"Transition from {po.status.value} to "
                    f"{status_update.status.value} is not allowed"
                )

            po.status = status_update.status
            await uow.commit()
            return await uow.purchase_orders.get_with_items(
                uow.session, organization_id, po.id
            )
