import uuid
from typing import List, Sequence, Tuple
from sqlalchemy.exc import IntegrityError
from app.services.base import BaseService
from app.models.product import Product, ProductStatus
from app.schemas.product import ProductCreate, ProductUpdate, ProductStatusUpdate
from app.services.exceptions import (
    ConflictDomainError,
    NotFoundDomainError,
    ValidationDomainError
)

class ProductService(BaseService):
    """
    Service for managing Product catalog lifecycle.
    Enforces financial-system rules, tenant isolation, and vendor ownership.
    """

    async def create_product(self, obj_in: ProductCreate) -> Product:
        """
        Create a new product.
        Rules:
        - SKU must be unique per tenant.
        - vendor_id must belong to the same tenant (if provided).
        - unit_price must be positive (enforced by schema).
        """
        async with self.uow:
            # 1. Vendor ownership validation
            if obj_in.vendor_id:
                vendor = await self.uow.vendors.get(self.uow.session, id=obj_in.vendor_id)
                if not vendor:
                    raise ValidationDomainError(
                        f"Vendor with ID {obj_in.vendor_id} not found or access denied."
                    )

            # 2. SKU uniqueness pre-check
            existing = await self.uow.products.get_by_sku(
                self.uow.session,
                sku=obj_in.sku
            )
            if existing:
                raise ConflictDomainError(
                    f"Product with SKU '{obj_in.sku}' already exists."
                )

            product_data = obj_in.model_dump()
            try:
                product = await self.uow.products.create(
                    self.uow.session,
                    obj_in=product_data
                )

                await self.record_audit(
                    action="CREATE",
                    resource_type="product",
                    resource_id=str(product.id),
                    payload=product_data
                )

                await self.uow.commit()
            except IntegrityError:
                raise ConflictDomainError(
                    f"Product with SKU '{obj_in.sku}' already exists."
                )
            return product

    async def get_product(self, product_id: uuid.UUID) -> Product:
        """
        Fetch a product by ID. Enforces tenant isolation.
        """
        async with self.uow:
            product = await self.uow.products.get(self.uow.session, id=product_id)
            if not product:
                raise NotFoundDomainError(f"Product with ID {product_id} not found.")
            return product

    async def list_products(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[Sequence[Product], int]:
        """
        List products with pagination. Enforces tenant isolation.
        """
        async with self.uow:
            items = await self.uow.products.get_multi(
                self.uow.session,
                skip=skip,
                limit=limit
            )
            total = await self.uow.products.count(self.uow.session)
            return items, total

    async def update_product(
        self, 
        product_id: uuid.UUID, 
        obj_in: ProductUpdate
    ) -> Product:
        """
        Update product details.
        Rule: SKU is immutable.
        """
        async with self.uow:
            product = await self.uow.products.get(self.uow.session, id=product_id)
            if not product:
                raise NotFoundDomainError(f"Product with ID {product_id} not found.")

            update_data = obj_in.model_dump(exclude_unset=True)
            
            # 1. Immutability enforcement
            update_data.pop("sku", None)
            update_data.pop("status", None)

            # 2. Vendor ownership validation if being updated
            if "vendor_id" in update_data and update_data["vendor_id"]:
                vendor = await self.uow.vendors.get(self.uow.session, id=update_data["vendor_id"])
                if not vendor:
                    raise ValidationDomainError(
                        f"Vendor with ID {update_data['vendor_id']} not found or access denied."
                    )

            updated_product = await self.uow.products.update(
                self.uow.session,
                db_obj=product,
                obj_in=update_data
            )

            await self.record_audit(
                action="UPDATE",
                resource_type="product",
                resource_id=str(product_id),
                payload=update_data
            )

            await self.uow.commit()
            return updated_product

    async def update_status(
        self, 
        product_id: uuid.UUID, 
        obj_in: ProductStatusUpdate
    ) -> Product:
        """
        Update product status (lifecycle management).
        """
        async with self.uow:
            product = await self.uow.products.get(self.uow.session, id=product_id)
            if not product:
                raise NotFoundDomainError(f"Product with ID {product_id} not found.")

            previous_status = product.status.value if product.status else None

            updated_product = await self.uow.products.update(
                self.uow.session,
                db_obj=product,
                obj_in={"status": obj_in.status}
            )

            await self.record_audit(
                action="STATUS_UPDATE",
                resource_type="product",
                resource_id=str(product_id),
                payload={
                    "previous_status": previous_status,
                    "status": obj_in.status.value
                }
            )

            await self.uow.commit()
            return updated_product
