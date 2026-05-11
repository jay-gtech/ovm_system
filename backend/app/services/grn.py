import uuid
from decimal import Decimal
from typing import List, Tuple
from app.models.grn import GRN, GRNLineItem, GRNStatus
from app.models.purchase_order import PurchaseOrderStatus
from app.models.audit_log import AuditAction
from app.schemas.grn import GRNCreate
from app.services.uow import BaseUnitOfWork
from app.services.exceptions import ServiceException

class GRNServiceError(ServiceException):
    pass

class GRNService:
    def __init__(self, uow: BaseUnitOfWork):
        self.uow = uow

    async def create_grn(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        grn_in: GRNCreate
    ) -> GRN:
        """Create a new GRN against a specific Purchase Order."""
        async with self.uow:
            # Validate PO exists and belongs to the organization
            po = await self.uow.purchase_orders.get_with_items(
                self.uow.session, 
                organization_id, 
                grn_in.po_id
            )
            if not po:
                raise GRNServiceError(f"Purchase Order {grn_in.po_id} not found")
            
            if po.status not in [PurchaseOrderStatus.APPROVED, PurchaseOrderStatus.SENT]:
                raise GRNServiceError(
                    f"Cannot create GRN for PO in status {po.status}"
                )
            
            # Create GRN Header
            grn = GRN(
                organization_id=organization_id,
                po_id=po.id,
                grn_number=grn_in.grn_number,
                receipt_date=grn_in.receipt_date,
                received_by=grn_in.received_by,
                warehouse_notes=grn_in.warehouse_notes,
                status=GRNStatus.DRAFT,
                total_received_qty=Decimal("0.0000"),
                created_by=user_id,
                updated_by=user_id
            )
            self.uow.session.add(grn)
            
            # We need the GRN ID to set on line items, so we flush
            await self.uow.session.flush()
            
            # Validate and create line items
            po_items_map = {item.id: item for item in po.line_items}
            total_qty = Decimal("0.0000")
            
            for item_in in grn_in.line_items:
                if item_in.po_line_item_id not in po_items_map:
                    raise GRNServiceError(
                        f"PO Line Item {item_in.po_line_item_id} not found in this PO"
                    )
                
                # Retrieve all previous GRNs for this PO to calculate pending quantity
                # Assuming pending quantity = po_item.quantity - sum(previous grn_item.qty_received)
                previous_grns = await self.uow.grns.list_by_po_id(self.uow.session, organization_id, po.id)
                previous_received = sum(
                    gli.qty_received 
                    for pgrn in previous_grns if pgrn.status != GRNStatus.CANCELLED
                    for gli in pgrn.line_items if gli.po_line_item_id == item_in.po_line_item_id
                )
                
                po_item = po_items_map[item_in.po_line_item_id]
                pending_qty = po_item.quantity - previous_received
                
                if item_in.qty_received > pending_qty:
                    raise GRNServiceError(
                        f"Cannot receive {item_in.qty_received}. Only {pending_qty} pending for {item_in.product_code}"
                    )
                
                grn_item = GRNLineItem(
                    organization_id=organization_id,
                    grn_id=grn.id,
                    po_line_item_id=item_in.po_line_item_id,
                    product_code=item_in.product_code,
                    qty_ordered=po_item.quantity,
                    qty_received=item_in.qty_received,
                    qty_damaged=item_in.qty_damaged,
                    qty_pending=pending_qty - item_in.qty_received,
                    created_by=user_id,
                    updated_by=user_id
                )
                self.uow.session.add(grn_item)
                total_qty += item_in.qty_received
            
            grn.total_received_qty = total_qty
            
            # Audit log
            await self.uow.audit_logs.log_action(
                self.uow.session,
                organization_id=organization_id,
                user_id=user_id,
                action=AuditAction.CREATE,
                resource_type="GRN",
                resource_id=grn.id,
                details={"grn_number": grn.grn_number, "po_id": str(po.id)}
            )
            
            await self.uow.commit()
            return grn

    async def complete_receipt(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        grn_id: uuid.UUID
    ) -> GRN:
        """Mark a GRN as completed."""
        async with self.uow:
            grn = await self.uow.grns.get_with_items(self.uow.session, organization_id, grn_id)
            if not grn:
                raise GRNServiceError(f"GRN {grn_id} not found")
            
            if grn.status != GRNStatus.DRAFT:
                raise GRNServiceError(f"GRN is already in status {grn.status}")
                
            grn.status = GRNStatus.COMPLETED
            grn.updated_by = user_id
            
            # Audit log
            await self.uow.audit_logs.log_action(
                self.uow.session,
                organization_id=organization_id,
                user_id=user_id,
                action=AuditAction.UPDATE,
                resource_type="GRN",
                resource_id=grn.id,
                details={"status": GRNStatus.COMPLETED.value}
            )
            
            await self.uow.commit()
            return grn

    async def partial_receipt(
        self,
        organization_id: uuid.UUID,
        user_id: uuid.UUID,
        grn_id: uuid.UUID
    ) -> GRN:
        """Handles partial receipt by verifying quantities and keeping PO open.
        Actually, completing the GRN implies the receipt is final for THIS document.
        The PO remains active until all items are fully received.
        """
        # A partial receipt is just completing a GRN where the received qty < ordered qty.
        # The PO will remain SENT/APPROVED because we aren't mutating the PO status to CLOSED here.
        # So we can just delegate to complete_receipt.
        return await self.complete_receipt(organization_id, user_id, grn_id)

    async def validate_receipt_quantities(
        self,
        organization_id: uuid.UUID,
        po_id: uuid.UUID
    ) -> Tuple[bool, List[dict]]:
        """
        Validates if all line items in a PO have been fully received.
        Returns a tuple: (is_fully_received, list_of_pending_items)
        """
        async with self.uow:
            po = await self.uow.purchase_orders.get_with_items(self.uow.session, organization_id, po_id)
            if not po:
                raise GRNServiceError(f"Purchase Order {po_id} not found")
                
            grns = await self.uow.grns.list_by_po_id(self.uow.session, organization_id, po_id)
            
            pending_items = []
            is_fully_received = True
            
            for po_item in po.line_items:
                received = sum(
                    gli.qty_received 
                    for grn in grns if grn.status == GRNStatus.COMPLETED
                    for gli in grn.line_items if gli.po_line_item_id == po_item.id
                )
                
                pending = po_item.quantity - received
                if pending > 0:
                    is_fully_received = False
                    pending_items.append({
                        "po_line_item_id": str(po_item.id),
                        "product_code": po_item.product_sku_snapshot,
                        "ordered": float(po_item.quantity),
                        "received": float(received),
                        "pending": float(pending)
                    })
                    
            return is_fully_received, pending_items
