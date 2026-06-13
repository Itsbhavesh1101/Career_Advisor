from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin, get_db
from app.schemas.admin_management import (
    AdminManagedItemCreate,
    AdminManagedItemPageRead,
    AdminManagedItemRead,
    AdminManagedItemStatus,
    AdminManagedItemType,
    AdminManagedItemUpdate,
)
from app.services.admin_management_service import AdminManagementService

router = APIRouter(prefix="/admin/management", tags=["admin-management"])


@router.get("/items", response_model=AdminManagedItemPageRead)
def list_admin_managed_items(
    item_type: AdminManagedItemType | None = Query(default=None),
    status_filter: AdminManagedItemStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
) -> AdminManagedItemPageRead:
    return AdminManagementService(db).list_items(
        item_type=item_type,
        status=status_filter,
    )


@router.post(
    "/items",
    response_model=AdminManagedItemRead,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_managed_item(
    payload: AdminManagedItemCreate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
) -> AdminManagedItemRead:
    try:
        return AdminManagementService(db).create_item(payload, user_id=admin.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.patch("/items/{item_id}", response_model=AdminManagedItemRead)
def update_admin_managed_item(
    item_id: int,
    payload: AdminManagedItemUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
) -> AdminManagedItemRead:
    try:
        return AdminManagementService(db).update_item(item_id, payload, user_id=admin.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/items/{item_id}", response_model=AdminManagedItemRead)
def archive_admin_managed_item(
    item_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
) -> AdminManagedItemRead:
    try:
        return AdminManagementService(db).archive_item(item_id, user_id=admin.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
