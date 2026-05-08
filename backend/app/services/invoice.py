import uuid
from decimal import Decimal, ROUND_HALF_UP
from typing import List
from app.models.invoice import Invoice, InvoiceLineItem, InvoiceStatus
from app.models.vendor import VendorStatus
from app.models.product import ProductStatus
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceStatusUpdate
from app.services.audit import AuditService
from app.services.base import BaseService
from app.services.exceptions import (
    ResourceNotFoundException,
    BusinessRuleViolationException,
    UnauthorizedException
)
from app.core.context import get_tenant_id

_FOUR_DP = Decimal("0.0001")

# Allowlist of valid Invoice status transitions.
_VALID_TRANSITIONS: dict[InvoiceStatus, set[InvoiceStatus]] = {
    InvoiceStatus.DRAFT: {InvoiceStatus.ISSUED, InvoiceStatus.CANCELLED},
    InvoiceStatus.ISSUED: {InvoiceStatus.PAID, InvoiceStatus.CANCELLED},
    InvoiceStatus.PAID: set(),
    InvoiceStatus.CANCELLED: set(),
}


class InvoiceService(BaseService):
    """
    Service layer for Invoice management.
    Handles orchestration, financial rules, tenant validation, and audit logging.
    """

    async def create_invoice(
        self,
        data: InvoiceCreate
    ) -> Invoice:
        """
        Create a new Invoice with line items.

        Financial Rules:
        - invoice_number must be unique per tenant.
        - vendor_id must belong to the tenant and be ACTIVE.
        - purchase_order_id (if provided) must belong to the tenant.
        - product_ids must belong to the tenant and be ACTIVE.
        - Snapshots generated from DB data at creation time.
        - All totals calculated server-side; client values ignored.
        """
        organization_id = get_tenant_id()
        if not organization_id:
            raise UnauthorizedException("Organization context missing")

        async with self.uow as uow:
            # 1. Validate Invoice number uniqueness within tenant
            existing_invoice = await uow.invoices.get_by_invoice_number(
                uow.session, organization_id, data.invoice_number
            )
            if existing_invoice:
                raise BusinessRuleViolationException(
                    f"Invoice number {data.invoice_number} already exists"
                )

            # 2. Validate vendor
            vendor = await uow.vendors.get(uow.session, data.vendor_id)
            if not vendor or vendor.organization_id != organization_id:
                raise ResourceNotFoundException("Vendor", data.vendor_id)
            if vendor.is_deleted or vendor.status != VendorStatus.ACTIVE:
                raise BusinessRuleViolationException(
                    "Cannot create invoice for an inactive or deleted vendor"
                )

            # 3. Validate Purchase Order (optional)
            if data.purchase_order_id:
                po = await uow.purchase_orders.get(uow.session, data.purchase_order_id)
                if not po or po.organization_id != organization_id:
                    raise ResourceNotFoundException("PurchaseOrder", data.purchase_order_id)
                if po.is_deleted:
                    raise BusinessRuleViolationException("Purchase Order is deleted")

            # 4. Process line items
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

                line_item = InvoiceLineItem(
                    organization_id=organization_id,
                    product_id=product.id,
                    product_sku_snapshot=product.sku,
                    product_name_snapshot=product.name,
                    unit_price_snapshot=product.unit_price,
                    quantity_snapshot=item_data.quantity,
                    line_total=line_total
                )
                line_item_models.append(line_item)

            # 5. Create Invoice header
            invoice = Invoice(
                organization_id=organization_id,
                invoice_number=data.invoice_number,
                vendor_id=data.vendor_id,
                purchase_order_id=data.purchase_order_id,
                due_date=data.due_date,
                status=InvoiceStatus.DRAFT,
                subtotal_amount=subtotal,
                total_amount=subtotal,  # No tax/shipping in foundation
                notes=data.notes,
                line_items=line_item_models
            )

            uow.session.add(invoice)

            # Audit: invoice.id is available immediately (Python UUID default)
            await AuditService.log_event(
                uow.session,
                entity_type="invoice",
                entity_id=invoice.id,
                action="INVOICE_CREATED",
                metadata={
                    "invoice_number": invoice.invoice_number,
                    "vendor_id": str(invoice.vendor_id),
                    "total_amount": str(subtotal),
                    "purchase_order_id": str(invoice.purchase_order_id) if invoice.purchase_order_id else None,
                    "line_item_count": len(line_item_models),
                },
            )

            await uow.commit()

            return await uow.invoices.get_with_items(
                uow.session, organization_id, invoice.id
            )

    async def get_invoice(self, id: uuid.UUID) -> Invoice:
        """Retrieve an invoice by ID with tenant validation and eager line-item loading."""
        organization_id = get_tenant_id()
        if not organization_id:
            raise UnauthorizedException("Organization context missing")
        async with self.uow as uow:
            invoice = await uow.invoices.get_with_items(uow.session, organization_id, id)
            if not invoice:
                raise ResourceNotFoundException("Invoice", id)
            return invoice

    async def list_invoices(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """List invoices for the current tenant."""
        async with self.uow as uow:
            return await uow.invoices.get_multi(uow.session, skip=skip, limit=limit)

    async def update_invoice(
        self,
        id: uuid.UUID,
        data: InvoiceUpdate
    ) -> Invoice:
        """
        Update mutable invoice fields (notes, due_date).
        Permitted in DRAFT and ISSUED states to support Net-15/30/45/60 workflows.
        Uses model_fields_set so omitted fields are never touched.
        Only logs field-level audit entries when the value actually changes.
        """
        organization_id = get_tenant_id()
        if not organization_id:
            raise UnauthorizedException("Organization context missing")
        async with self.uow as uow:
            invoice = await uow.invoices.get_with_items(uow.session, organization_id, id)
            if not invoice:
                raise ResourceNotFoundException("Invoice", id)
            if invoice.status not in {InvoiceStatus.DRAFT, InvoiceStatus.ISSUED}:
                raise BusinessRuleViolationException(
                    f"Invoice fields cannot be updated in {invoice.status.value} status"
                )

            # Capture old values before mutation for accurate diff logging
            old_due_date = invoice.due_date
            old_notes = invoice.notes

            if "due_date" in data.model_fields_set:
                invoice.due_date = data.due_date
                if old_due_date != data.due_date:
                    await AuditService.log_event(
                        uow.session,
                        entity_type="invoice",
                        entity_id=invoice.id,
                        action="INVOICE_UPDATED",
                        field_name="due_date",
                        old_value=str(old_due_date) if old_due_date else None,
                        new_value=str(data.due_date) if data.due_date else None,
                    )

            if "notes" in data.model_fields_set:
                invoice.notes = data.notes
                if old_notes != data.notes:
                    await AuditService.log_event(
                        uow.session,
                        entity_type="invoice",
                        entity_id=invoice.id,
                        action="INVOICE_UPDATED",
                        field_name="notes",
                        old_value=old_notes,
                        new_value=data.notes,
                    )

            await uow.commit()
            return await uow.invoices.get_with_items(uow.session, organization_id, invoice.id)

    async def update_invoice_status(
        self,
        id: uuid.UUID,
        status_update: InvoiceStatusUpdate
    ) -> Invoice:
        """Update invoice status enforcing the allowlist state machine."""
        organization_id = get_tenant_id()
        if not organization_id:
            raise UnauthorizedException("Organization context missing")
        async with self.uow as uow:
            invoice = await uow.invoices.get_with_items(uow.session, organization_id, id)
            if not invoice:
                raise ResourceNotFoundException("Invoice", id)

            allowed = _VALID_TRANSITIONS.get(invoice.status, set())
            if status_update.status not in allowed:
                raise BusinessRuleViolationException(
                    f"Transition from {invoice.status.value} to "
                    f"{status_update.status.value} is not allowed"
                )

            old_status = invoice.status
            invoice.status = status_update.status

            action = (
                "INVOICE_CANCELLED"
                if status_update.status == InvoiceStatus.CANCELLED
                else "INVOICE_STATUS_CHANGED"
            )
            await AuditService.log_event(
                uow.session,
                entity_type="invoice",
                entity_id=invoice.id,
                action=action,
                field_name="status",
                old_value=old_status.value,
                new_value=status_update.status.value,
            )

            await uow.commit()
            return await uow.invoices.get_with_items(
                uow.session, organization_id, invoice.id
            )
