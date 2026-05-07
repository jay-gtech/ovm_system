import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, Query, status

from app.api import deps
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductStatusUpdate,
    ProductResponse,
    ProductListResponse
)
from app.services.product import ProductService
from app.services.uow import SQLAlchemyUnitOfWork

router = APIRouter()

@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    product_in: ProductCreate
) -> Any:
    """
    Create a new product.
    """
    service = ProductService(uow)
    return await service.create_product(product_in)

@router.get("/", response_model=ProductListResponse)
async def list_products(
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
) -> Any:
    """
    List products with pagination.
    """
    service = ProductService(uow)
    items, total = await service.list_products(skip=skip, limit=limit)
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    product_id: uuid.UUID
) -> Any:
    """
    Get product by ID.
    """
    service = ProductService(uow)
    return await service.get_product(product_id)

@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    product_id: uuid.UUID,
    product_in: ProductUpdate
) -> Any:
    """
    Update product details.
    """
    service = ProductService(uow)
    return await service.update_product(product_id, product_in)

@router.patch("/{product_id}/status", response_model=ProductResponse)
async def update_product_status(
    *,
    uow: SQLAlchemyUnitOfWork = Depends(deps.get_uow),
    product_id: uuid.UUID,
    status_in: ProductStatusUpdate
) -> Any:
    """
    Update product status (lifecycle).
    """
    service = ProductService(uow)
    return await service.update_status(product_id, status_in)
